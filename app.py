import os
import time
import pandas as pd
# from flask import Flask, request, jsonify,Response
from flask import Flask, redirect, request, session, url_for, jsonify,Response
from requests_oauthlib import OAuth1Session
from langchain.vectorstores import FAISS
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.question_answering import load_qa_chain
from langchain_openai import OpenAI
from flask_cors import CORS  
from constants.constants import pie_chart_config, line_graph_config, bar_chart_config
import pdfplumber
import json
import uuid
from io import BytesIO
import requests
app = Flask(__name__)
CORS(app,supports_credentials=True)
os.environ["OPENAI_API_KEY"] = ""
openai_model = OpenAI(max_tokens=1500, temperature=0.7)
import boto3
from botocore.exceptions import NoCredentialsError
AWS_ACCESS_KEY = ''  
AWS_SECRET_KEY = ''  
AWS_REGION = 'ap-south-1'  
BUCKET_NAME = ''
consumer_key = ''
consumer_secret = ''
callback_url = ''
# You will need to set a secret key for session management
app.secret_key = ''
@app.route('/auth/twitter')
def twitter_auth():
    # Create an OAuth1 session object with the consumer credentials
    oauth = OAuth1Session(consumer_key, client_secret=consumer_secret, callback_uri=callback_url)

    # Get the request token
    request_token = oauth.fetch_request_token('https://api.twitter.com/oauth/request_token')

    # Save the request token in the session for later use
    session['oauth_token'] = request_token['oauth_token']
    session['oauth_token_secret'] = request_token['oauth_token_secret']
    # print("OAuth Token Secret stored:", session.get('oauth_token_secret'))
    # Redirect the user to Twitter for authorization
    auth_url = oauth.authorization_url('https://api.twitter.com/oauth/authorize')
    return redirect(auth_url)

@app.route('/auth/twitter/callback', methods=['POST'])
def twitter_callback():
    # Retrieve the oauth_token and oauth_verifier from the POST request body
    data = request.json
    oauth_token = data.get('oauth_token')
    oauth_verifier = data.get('oauth_verifier')

    # Validate input
    if not oauth_token or not oauth_verifier:
        return jsonify({'error': 'Missing oauth_token or oauth_verifier'}), 400

    # Retrieve the request token secret from the session
    oauth_token_secret = session.get('oauth_token_secret')
    if not oauth_token_secret:
        return jsonify({'error': 'Session missing oauth_token_secret'}), 400

    # Create an OAuth1 session with the token and verifier
    oauth = OAuth1Session(
        consumer_key,
        client_secret=consumer_secret,
        resource_owner_key=oauth_token,
        resource_owner_secret=oauth_token_secret,
        verifier=oauth_verifier
    )

    try:
        # Get the access token from Twitter
        access_token_data = oauth.fetch_access_token('https://api.twitter.com/oauth/access_token')

        # Extract the access token and access token secret
        access_token = access_token_data.get('oauth_token')
        access_token_secret = access_token_data.get('oauth_token_secret')

        return jsonify({
            'access_token': access_token,
            'access_token_secret': access_token_secret
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION
)

# Function to generate a random name for the video
def generate_random_filename(extension='mp4'):
    return f"{uuid.uuid4().hex}.{extension}"

# Function to upload video to S3
def upload_video_to_s3(file_url, random_filename):
    try:
        # Download video from URL
        response = requests.get(file_url)
        if response.status_code != 200:
            raise Exception(f"Failed to download the file. Status code: {response.status_code}")
        
        # Upload to S3
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=random_filename,
            Body=BytesIO(response.content),
            ContentType='video/mp4',
            # ACL='public-read'  # Optional: to make the video publicly accessible
        )
        return f"https://{BUCKET_NAME}.s3.amazonaws.com/{random_filename}"
    except Exception as e:
        print(f"Error uploading video: {e}")
        return None

# Flask route to handle video upload and random filename generation
@app.route('/upload_video', methods=['POST'])
def upload_video():
    # Get the video URL from the request body
    data = request.get_json()
    video_url = data.get('video_url')
    if not video_url:
        return jsonify({"error": "video_url is required"}), 400
    
    # Generate a random file name
    random_filename = generate_random_filename()
    
    # Upload the video to S3
    video_url_in_s3 = upload_video_to_s3(video_url, random_filename)
    
    if video_url_in_s3:
        return jsonify({
            "success": True,
            "random_filename": random_filename,
            "s3_url": video_url_in_s3
        }), 200
    else:
        return jsonify({"error": "Failed to upload the video"}), 500


@app.route('/upload', methods=['POST'])
def upload_file():
    # Check if file is in the request
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']

    # If no file is selected
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # Generate a unique filename (you can modify this as per your requirement)
    file_name = file.filename
    try:
        # Upload file to S3
        s3_client.upload_fileobj(file, BUCKET_NAME, file_name)

        # Generate the S3 URL (URL format can vary depending on your setup)
        s3_url = f"https://{BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{file_name}"

        # Return the S3 URL in the response
        return jsonify({"s3_url": s3_url}), 200

    except FileNotFoundError:
        return jsonify({"error": "File not found"}), 400
    except NoCredentialsError:
        return jsonify({"error": "Credentials not available"}), 403
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def clean_llm_response(response):
    cleaned_response = response.replace('\\n', '').replace('\\t', '').replace('\\"', '"')
    cleaned_response = cleaned_response.strip()
    if not cleaned_response.startswith('{'):
        cleaned_response = '{' + cleaned_response
    if not cleaned_response.endswith('}'):
        cleaned_response = cleaned_response + '}'
    try:
        json_data = json.loads(cleaned_response)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to decode cleaned response as JSON: {e}")
    return json_data

def generate_echarts_code(csv_data, prompt=None, config=bar_chart_config):
    embeddings = OpenAIEmbeddings()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=32)
    texts = text_splitter.split_text(csv_data)
    docsearch = FAISS.from_texts(texts, embeddings)
    chain = load_qa_chain(openai_model, chain_type="stuff")
    backslash_char = "\\"
    echart_query = f'''
    I have the following CSV data:

    {csv_data}

    {"{backslash_char}n{backslash_char}nAdditional instructions:{backslash_char}n" + prompt if prompt else ""}

    Please analyze this data and provide me with a **final ECharts configuration in valid JSON format**, including:

    {config}
    Ensure that:
1. The output is strictly valid JSON.
2. Do not include any explanatory text outside the JSON object.
3. Validate the JSON format to avoid parsing errors.
4. Return only the JSON object of final echarts configuration.
    '''
    docs = docsearch.similarity_search(echart_query)
    response = chain.run(input_documents=docs, question=echart_query)
    cleaned_response = clean_llm_response(response)
    return cleaned_response

def generate_echarts_code_from_pdf(pdf_file, prompt=None, config=bar_chart_config):
    try:
        with pdfplumber.open(pdf_file) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore')
        if not text:
            raise ValueError("No text extracted from the PDF.")
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=32)
        texts = text_splitter.split_text(text)
        embeddings = OpenAIEmbeddings()
        docsearch = FAISS.from_texts(texts, embeddings)
        chain = load_qa_chain(openai_model, chain_type="stuff")
        backslash_char = "\\"
        query = f'''
        I have the following extracted text from a PDF document:

        {text}

        {"{backslash_char}n{backslash_char}nAdditional instructions:{backslash_char}n" + prompt if prompt else ""}

        Please analyze this data and provide me with a **final ECharts configuration in valid JSON format**, including
        {config}
        Ensure that:
1. The output is strictly valid JSON.
2. Do not include any explanatory text outside the JSON object.
3. Validate the JSON format to avoid parsing errors.
4. Return only the JSON object of final echarts configuration.
        '''
        docs = docsearch.similarity_search(query)
        response = chain.run(input_documents=docs, question=query)
        cleaned_response = clean_llm_response(response)
        return cleaned_response
    except Exception as e:
        raise RuntimeError(f"An error occurred while processing the PDF: {str(e)}")

def generate_echarts_code_from_txt(txt_data, prompt=None, config=bar_chart_config):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=32)
    texts = text_splitter.split_text(txt_data)
    embeddings = OpenAIEmbeddings()
    docsearch = FAISS.from_texts(texts, embeddings)
    backslash_char = "\\"
    chain = load_qa_chain(openai_model, chain_type="stuff")
    echart_query = f'''Analyze the following text data and identify statistical data that can be visualized in an ECharts chart.

    Text Data:
    {txt_data}
    {"{backslash_char}n{backslash_char}nAdditional instructions:{backslash_char}n" + prompt if prompt else ""}
    Please analyze this data and provide me with a **final ECharts configuration in valid JSON format**, including
    {config}
    Ensure that:
1. The output is strictly valid JSON.
2. Do not include any explanatory text outside the JSON object.
3. Validate the JSON format to avoid parsing errors.
4. Return only the JSON object of final echarts configuration.
    '''
    docs = docsearch.similarity_search(echart_query)
    response = chain.run(input_documents=docs, question=echart_query)
    cleaned_response = clean_llm_response(response)
    return cleaned_response

def generate_echarts_code_from_prompt(prompt, config=bar_chart_config):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=32)
    texts = text_splitter.split_text(prompt)
    embeddings = OpenAIEmbeddings()
    docsearch = FAISS.from_texts(texts, embeddings)
    chain = load_qa_chain(openai_model, chain_type="stuff")
    echart_query = f'''Analyze the following text data and identify statistical data that can be visualized in an ECharts chart.

    Text Data:
    {prompt}

    Please analyze this data and provide me with a **final ECharts configuration in valid JSON format**, including
    {config}
    Ensure that:
1. The output is strictly valid JSON.
2. Do not include any explanatory text outside the JSON object.
3. Validate the JSON format to avoid parsing errors.
4. Return only the JSON object of final echarts configuration.
    '''
    docs = docsearch.similarity_search(echart_query)
    response = chain.run(input_documents=docs, question=echart_query)
    cleaned_response = clean_llm_response(response)
    return cleaned_response

@app.route('/generate-echarts', methods=['POST'])
def generate_echarts():
    # file = ''
    file = request.files.get('file')
    prompt = request.form.get('prompt', '')
    if not file and not prompt:
        return jsonify({"error": "No file or prompt provided"}), 400
    config = ''
    if prompt:
        if 'bar chart' in prompt.lower():
            config = bar_chart_config
        elif 'pie chart' in prompt.lower():
            config = pie_chart_config
        elif 'line chart' in prompt.lower():
            config = line_graph_config
    try:
        if not file:
            if not prompt:
                return jsonify({"error": "No file or prompt provided"}), 400
            echarts_code = generate_echarts_code_from_prompt(prompt, config)
        else:
            # file_extension = 'txt'
            file_extension = file.filename.split('.')[-1].lower()
            if file_extension == 'csv':
                df = pd.read_csv(file)
                csv_data = df.to_string(index=False)
                echarts_code = generate_echarts_code(csv_data, config)
            elif file_extension == 'pdf':
                echarts_code = generate_echarts_code_from_pdf(file, config)
            elif file_extension == 'txt':
                # with open(file, 'r', encoding='utf-8') as f:
                #     txt_data = f.read()
                txt_data = file.read().decode('utf-8')
                echarts_code = generate_echarts_code_from_txt(txt_data, config)
            else:
                return jsonify({"error": "Unsupported file type"}), 400
        return jsonify({"echarts_code": echarts_code})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/hello', methods=['GET'])
def hello_world():
    return "Hello, World!"

@app.route('/webhook', methods=['POST'])
def webhook():
    # Receive JSON data from the client (POST request)
    data = request.get_json()
    if not data or 'id' not in data or 'url' not in data:
        return jsonify({"error": "Invalid data. 'id' and 'url' are required."}), 400

    id = data.get('id')
    url = data.get('url')

    # Store the received data in a global dictionary (or use a more persistent store like Redis)
    print(url)
    stored_data['id'] = id
    stored_data['url'] = url

    return jsonify({"message": "Data received successfully."}), 200
stored_data = {}
@app.route('/sse', methods=['GET'])
def sse():
    def event_stream():
        try:
            while True:
                if stored_data:  # Check if there is data to send
                    # Send the stored data as an SSE event
                    yield f"data: {json.dumps({'id': stored_data['id'], 'url': stored_data['url']})}\n\n"

                    # After sending the data, clear the stored_data
                    stored_data.clear()

                    time.sleep(1)  # Simulate a delay before sending the next message
                else:
                    time.sleep(5)
                  # Simulate a delay before sending the next message
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(event_stream(), content_type='text/event-stream')


if __name__ == '__main__':
    app.run(debug=True)


