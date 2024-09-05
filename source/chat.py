import csv
import time
from typing import List
from csv_tool import write_to_csv
from langchain.memory import ConversationBufferWindowMemory, ConversationBufferMemory
from source.retriever import get_context
from configs.load_config import LoadConfig
from source.utils.base_model import GradeReWrite, Product, Seaching, Stage, ProductList, OrderDetails
from source.utils.prompt import PROMPT_HISTORY, PROMPT_HEADER, PROMPT_ELS_OR_TEXT, PROMPT_STAGE, template, PROMPT_HEADER_S2, PROMPT_HEADER_S3, PROMPT_HEADER_S1
from source.utils.prompt2 import PROMPT_STAGE_SEARCHING
from rag_architecture.few_shot_sentence import classify_intent
from rag_architecture.retrieval import search_db
from langchain.prompts import PromptTemplate
from langchain.chains import ConversationChain

APP_CFG = LoadConfig()
memory = ConversationBufferWindowMemory(memory_key="chat_history", k = 3)

def get_history():
    history = memory.load_memory_variables({})
    return history['chat_history']

def rewrite_query(query: str, history: str) -> str: 
    """
    Arg:
        query: câu hỏi của người dùng
        history: lịch sử của người dùng
        Sử dụng LLM để viết lại câu hỏi của người dùng thành 1 câu mới.
    Return:
        trả về câu hỏi được viết lại.
    """
    query_rewrite_prompt = PromptTemplate(
        input_variables=["question", "chat_history"],
        template=PROMPT_HISTORY
    )
    llm_with_output = APP_CFG.load_rewrite_model().with_structured_output(GradeReWrite)
    
    query_rewriter = query_rewrite_prompt | llm_with_output
    
    query_rewrite = query_rewriter.invoke({"question": query, "chat_history": history}).rewrite
    
    #llm_with_output = APP_CFG.load_rewrite_model().with_structured_output(GradeReWrite)
    #query_rewrite = llm_with_output.invoke(PROMPT_HISTORY.format(question=query, chat_history=history)).rewrite
    
    return query_rewrite

def decision_search_type(query: str) -> str: 
    llm_with_output = APP_CFG.load_rewrite_model().with_structured_output(Seaching)
    type = llm_with_output.invoke(PROMPT_ELS_OR_TEXT.format(query=query)).type
    return type

def decision_stage_type(query: str, history: str) -> str: 
    llm_with_output = APP_CFG.load_rewrite_model().with_structured_output(Stage)
    type = llm_with_output.invoke(PROMPT_STAGE.format(query=query, chat_history = history)).type
    return type

from source.retriever import get_tool
import numpy as np 

def chat_with_history_2(query: str, history: str):
    start_time_1 = time.time()
    print("-Start-")
    history_conversation = get_history()
    print(history_conversation)
    print("-" * 20)
    query_rewrite = rewrite_query(query=query, history=history_conversation)
    # query_rewrite = "Câu hỏi gốc: " + query + " Câu hỏi được viết lại: " + query_rewrite
    # query_rewrite = rewrite_query(query=query, history=history_conversation)
    print(query_rewrite)
    print("-" * 30)
    
    type = decision_search_type(query_rewrite)
    print(type)
    if "ELS" in type:
        demands = classify_intent(query_rewrite)
        print("= = = = result few shot = = = =:", demands)
        if len(demands['object']) >= 1:
            response_elastic, products = search_db(demands)
            save_outtext = response_elastic
        else: 
            save_outtext = ""
        prompt_final = PROMPT_HEADER.format(question=query_rewrite, context=save_outtext)
        
    else:
        context = get_context(query=query_rewrite)
        print("===== CONTEXT =====")
        print(context)
        prompt_final = PROMPT_HEADER.format(question=query_rewrite, context=context)

    response = APP_CFG.load_rag_model().invoke(prompt_final)

    print(response)
    print("-Finish-")
    
    memory.chat_memory.add_user_message(query)
    memory.chat_memory.add_ai_message(response)

    history.append((query, response))
    print("Total time used:", time.time() - start_time_1)
    return response, history

import json

def close_order(query: str, history: str, detail_info: str):
    
    # print("=== Memory Close Order ===", memory)
    
    prompt = template.format(history = history, input = query, detail_info = detail_info)
    llm = APP_CFG.load_rag_model().with_structured_output(OrderDetails)
    # llm = llm.bind_tool(fill_csv)
    response = llm.invoke(prompt)

    print( "RESPONSE: ", response.Intent)
    return response

def chat_with_history_1(query: str, history):
    start_time = time.time()
    print("==== HISTORY CONVERSATION ====")
    history_conversation = get_history()
    print(history_conversation)
    print("==== QUERY REWRITE ====")
    # query_rewrite = query
    query_rewrite = rewrite_query(query=query, history=history_conversation)
    query_rewrite = "Câu hỏi gốc: " + query + " Câu hỏi được viết lại: " + query_rewrite
    print(query_rewrite)
    print("==== STAGE DECISION ====")
    stage = decision_stage_type(query= query_rewrite, history = history_conversation)
    print(stage)
    print("==== SEARCH DECISION ====")
    if "S2" in stage:
        context = close_order(query=query_rewrite, history=history_conversation)
        # print(query_rewrite)
        # products_info = ""
        # for product in context.ProductList:
        #    product_name = product.ProductName
        #    price = product.Price
        #    products_info += get_context(query = product_name + "có giá" + str(price), top_k = 2)

        prompt_final = PROMPT_HEADER_S2.format(question=query_rewrite, context = context)
    else:
        type = decision_search_type(query_rewrite)
        if "ELS" in type:
            print("==== ELASTIC SEARCH =====")
            demands = classify_intent(query_rewrite)
            print("= = = = result few short = = = =:", demands)
            if len(demands['object']) >= 1:
                response_elastic, products = search_db(demands)
                save_outtext = response_elastic
            else: 
                save_outtext = ""
            prompt_final = PROMPT_HEADER.format(question=query_rewrite, context=save_outtext)
            
        else:
            print("==== TEXT SEARCH =====")
            context = get_context(query=query_rewrite)
            print("\t===== CONTEXT: =====")
            print(context)
            prompt_final = PROMPT_HEADER.format(question=query_rewrite, context=context)

    response = APP_CFG.load_rag_model().invoke(prompt_final).content

    print("==== RESPONSE =====")
    print(response)
    print("Time used:", time.time() - start_time)
    print("==== FINISH ====")
    
    memory.chat_memory.add_user_message(query)
    memory.chat_memory.add_ai_message(response)

    history.append((query, response))

    return "", history

# response = chat_with_history(query="Tôi muốn mua điều hòa")
# print(response)


import pandas as pd

def Extract_Products(orders: OrderDetails, xlsx_file_path: str):
    # Read the Excel file into a DataFrame
    df = pd.read_excel(xlsx_file_path)
    
    # Initialize an empty string to collect matching product details
    product_list_str = ""
    
    for product in orders.ProductList:
        print(product.ProductName)
        # Check if the product name matches any in the Excel file
        matching_rows = df[df['product_name'] == product.ProductName]
        
        if not matching_rows.empty:
            for _, row in matching_rows.iterrows():
                product_name = row['product_name']
                lifecare_price = row['lifecare_price']
                product_info = row['product_info']
                specification = row['specification']
                
                # Add the product details to the string
                product_list_str += (f"Product Name: {product_name}, "
                                     f"Lifecare Price: {lifecare_price}, "
                                     f"Product Info: {product_info}, "
                                     f"Specification: {specification}\n")
    
    return product_list_str

def chat_with_history(query: str, history: str):
    start_time_1 = time.time()
    # global response
    # print("==== HISTORY CONVERSATION ====")
    history_conversation = get_history()
    # print(history_conversation)
    # print("==== QUERY REWRITE ====")
    print("Get history:", time.time() - start_time_1)
    start_time = time.time()
    
    query_rewrite = rewrite_query(query=query, history=history_conversation)
    query_rewrite_combine = "Câu hỏi gốc: " + query + "\nCâu hỏi được viết lại: " + query_rewrite + "\n"
    # print(query_rewrite)
    # print("==== STAGE & SEARCHING DECISION ====:")
    print("Get rewrite:", time.time() - start_time)
    start_time = time.time()
    
    llm_with_output = APP_CFG.load_rewrite_model().with_structured_output(OrderDetails)
    json_response = llm_with_output.invoke(PROMPT_STAGE_SEARCHING.format(query=query_rewrite, chat_history = history))
    if json_response.FullName.lower() in ["anh", "chị", "khách hàng"]:
        json_response.FullName = ""
    # print(json_response)
    print("JSON:", time.time() - start_time)
    start_time = time.time()
    
    # csv_file_path = "data\product_final_300_extract.xlsx"
    # matched_products_str = Extract_Products(json_response, csv_file_path)
    # print("==== PRODUCTS INFORMATION ====:")
    # print(matched_products_str)
    
    # print("==== SEARCH DECISION ====:")
    # print(json_response.RetrieveDecision.type)
    context = ""
    if json_response.RetrieveDecision.type == "TEXT":
        # print("==== TEXT SEARCH ====:")
        context = get_context(query=query_rewrite)
        #print("\t===== CONTEXT: =====")
        #print(context)
    elif json_response.RetrieveDecision.type == "ELS":
        # print("==== ELASTIC SEARCH =====:")
        demands = classify_intent(query_rewrite)
        # print("= = = = result few short = = = =:", demands)
        if len(demands['object']) >= 1:
            response_elastic, products = search_db(demands)
            context = response_elastic
    print("Search:", time.time() - start_time)
    start_time = time.time()
        
    if context == "": context = "Hãy dựa vào các thông tin khác để trả lời câu hỏi"
    if json_response.Intent.type == "S1":
        # print("==== CONSULTANT ====")
        prompt_final = PROMPT_HEADER_S1.format(question=query_rewrite_combine, context=context)
    elif json_response.Intent.type == "S2":
        # print("==== CLOSE DEAL ====")
        prompt_final = PROMPT_HEADER_S2.format(question=query_rewrite_combine, context = context, json_details = json_response)
    elif json_response.Intent.type == "S3":
        # print("==== TRACK ORDER DETAILS ====")
        prompt_final = PROMPT_HEADER_S3.format(question=query_rewrite_combine, context = context, json_details = json_response)
    print("Prompting:", time.time() - start_time)
    start_time = time.time()
    
    response = APP_CFG.load_rag_model().invoke(prompt_final).content

    # print("==== RESPONSE =====")
    # print(response)
    
    #print(memory)
    #print("==== MEMORY 1 ====")
    memory.chat_memory.add_user_message(query)
    memory.chat_memory.add_ai_message(response)
    # memory.chat_memory.add_ai_message(response)
    # memory.chat_memory.add_system_message(context)
    # print(memory)
    # print("==== MEMORY 2 ====")
    
    history.append((query, response))
    #print(history)
    #print("==== HISTORY 1 ====")
    print("Response used:", time.time() - start_time)
    print("Total time used:", time.time() - start_time_1)
    #print("==== FINISH ====")
    return "", history