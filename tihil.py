import streamlit as st
import os
from groq import Groq
from dotenv import load_dotenv
import pandas as pd
import requests


if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


API_KEY = os.getenv("API_KEY")

def fetch_shopping_results(prod):
    url = "https://serpapi.com/search"
    params = {
        "engine": "google_shopping",
        "q": prod,
        "hl": "en",
        "api_key": API_KEY
    }

    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        return data.get("shopping_results", [])
    else:
        return []


# Load environment variables
load_dotenv()

# Set DeepSeek API key
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
# Function to call DeepSeek API
def call_deepseek_api(response: str, country: str,product: str,quant: str) -> str:
    
    # Create a prompt for DeepSeek
    prompt = f"What is the Average Selling Price (ASP) for the item with HSN code {response} and product name is {product} and quantity is {quant} in {country}? Provide the ASP in rupees. Ensure that the ASP remains the same for repeated queries with the same HSN code and country. Do not introduce variability—return the consistent value from a reliable source or database. Only provide the price without additional explanations or formatting changes."  
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
    )
    response = chat_completion.choices[0].message.content
    return response

def api1(response: str, country: str,product: str,quant: str) -> str:
    
    # Create a prompt for DeepSeek
    prompt = f"What is the Average Selling Price (ASP) for the item with HSN code {response} and product name is {product} and quantity is {quant} in {country}? Provide the ASP in rupees. Ensure that the ASP remains the same for repeated queries with the same HSN code and country. Do not introduce variability—return the consistent value from a reliable source or database. Only provide the price without additional explanations or formatting changes."
    
    
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="mixtral-8x7b-32768",
    )
    response = chat_completion.choices[0].message.content
    return response

def api2(response: str, country: str,product: str ,quant: str) -> str:
    
    # Create a prompt for DeepSeek
    prompt = f"What is the Average Selling Price (ASP) for the item with HSN code {response} and product name is {product} and quantity is {quant} in {country}? Provide the ASP in rupees.only provide the price dont give the text only price in rupees, do not change the response at refreshing for same params give the proper value"
    
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="deepseek-r1-distill-qwen-32b",
    )
    response = chat_completion.choices[0].message.content
    return response
    

# Streamlit App
st.title("HSN Code ASP Chatbot")
st.write("Enter the HSN code and destination country to get the Average Selling Price (ASP).")


def load_data():
    df = pd.read_excel("100hsncode.xlsx", skiprows=2)  # Skip first two rows
    df = df.iloc[:, 1:3]  # Select only the relevant two columns
    df.columns = ["HSN Code", "Description"]  # Rename columns
    df.dropna(inplace=True)  # Remove empty rows
    df["HSN Code"] = df["HSN Code"].astype(int).astype(str)  # Convert HSN Code to string for matching
    return df
df = load_data()
# Function to get description from HSN code
def get_hsn_description(hsn_code, df):
    result = df[df["HSN Code"] == hsn_code]  # Assuming column name is 'HSN Code'
    return result["Description"].values[0] if not result.empty else "HSN Code not found"

# Input fields
product = st.text_input("Enter product name Code:", placeholder="e.g., bricks")
quant = st.text_input("Enter product quantity Code:", placeholder="e.g., 100")
hsn_code = st.text_input("Enter HSN Code:", placeholder="e.g., 1234")
description = get_hsn_description(hsn_code, df)

country = st.text_input("Enter Destination Country:", placeholder="e.g., USA")

def generalize(desc,hsn_code,product):
    # Create a prompt for DeepSeek
    prompt = f"take the description and give me the llm model names and the average selling prices given in the description in proper table format ,table has contain product name{product} ,hsn code{hsn_code} and llama ,mistral,deepseek and serpapi ,these are the coloumns ok ,give me the table only dont give any other things from description things ASP for 4 models llama ,mistral,deepseek and serpapi  , Description:{desc} ,table is of two rows in 1 all the fields name and in second row values for it   "
    
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
    )
    response = chat_completion.choices[0].message.content
    return response
    
# Button to fetch ASP
if st.button("Get ASP"):
    if description and country and product:
        try:
            prompt = f"What is the product it is in the description {product} and this is the hsn code {hsn_code} give me the name of product no more info only product name "

            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
            )
            response = chat_completion.choices[0].message.content
            print(response)
            summary=[]

            asp_response = call_deepseek_api(hsn_code, country, product,quant)
            summary.append("llama-3.3-70b "+asp_response)
            # st.success(f"ASP for HSN Code through llama  {hsn_code} in {country}: {asp_response}")
            asp_response2 = api1(hsn_code, country,product,quant)
            summary.append("mistral-8x7b "+asp_response2)
            
            asp_response3 = api2(hsn_code, country,product,quant)
            summary.append("deepseek-r1 "+asp_response3)
            

            

            
            
            # Fetch data and extract prices
            data = fetch_shopping_results(product+" "+quant)
            prices = [item["price"] for item in data[:40] if "price" in item]

            prompt = f"What is the average of these numbers {prices} and convert in rupees ,only give average dont add other things in response   ."

            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
            )
            response = chat_completion.choices[0].message.content
            summary.append("serpapi "+response)
            

            resp=generalize(summary,hsn_code,product)
            st.session_state.chat_history.append({"user": hsn_code ,"country":country, "bot": resp})
            st.write(resp)
    
        except Exception as e:
            st.error(f"An error occurred: {e}")
    for chat in st.session_state.chat_history:
        # st.write(f"**You:** {chat['user']} {chat['country']}")
        st.write(f"**Bot:** ")
        st.write(chat['bot'])
    else:
        st.warning("Please enter both product name ,HSN code and destination country.")
