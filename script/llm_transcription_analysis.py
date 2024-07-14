import pandas as pd
import openai
import random
import json


def get_summary(transcript, openai_config):

    openai.api_type = openai_config['openai_api_type']
    openai.api_base = openai_config['openai_api_base']
    openai.api_version = openai_config['openai_api_version']
    openai.api_key = openai_config['openai_api_key']

    txt = openai.ChatCompletion.create(
        messages = [
            {
                "role": "system",
                "content": f"""
                Record meeting minutes from a meeting recording. \
                You are given the transcript of the meeting, and you need to capture the key points discussed. \
                And generate a summary. The summary should be concise, represented as bullet points. \
                Follow the user expected output format. \
                Respond in English, even if the transcript is in Chinese. \
                """,
            },
            {
                "role": "user", 
                "content": f"""
                ```{chr(123)}expected format{chr(125)}

                Meeting Summary:
                <list of summaries>
                ```
                 
                ```{chr(123)}transcript{chr(125)}
                {transcript}
                ```
                """
            }
        ],
        engine=openai_config['openai_model_engine'],
        temperature=.1,
        top_p=.5,
        max_tokens=2048,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None,
    )['choices'][0]["message"]["content"]
    
    html = openai.ChatCompletion.create(
        messages = [
            {
                "role": "system",
                "content": f"""
                User will provide a meeting summary (delimited with XML tags <summary></summary>), and you need to convert them into HTML format. \
                Your output should be in the <div> and should only include syntax used in HTML. \
                Which mean you should ignore the <body> since you would be embedded into another parent <div>
                """,
            },
            {
                "role": "user", 
                "content": f"""<summary><{txt}/summary>"""
            }
        ],
        engine=openai_config['openai_model_engine'],
        temperature=.1,
        top_p=.5,
        max_tokens=2048,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None,
    )['choices'][0]["message"]["content"]
    
    sample_txt = """The Youth Association's chosen representative seeks writing guidance from Zhang Laoshi. They discuss the importance of well-being and world connection. They note the Association's activities aimed at gaining deeper understanding. Zhang Laoshi advises the article should cover personal growth, social environment, and personal identity, focusing on clarity, brevity, and confidence."""
    mindmap = openai.ChatCompletion.create(
        messages = [
            {
                "role": "system",
                "content": f"""
                You are given meeting summary (delimited with XML tags <summary></summary>), and your task is to understand the main idea discussed and only generalise the main idea in a tree data format. \
                The relevant idea should be connected with each other as the form of Topic and sub topic so that could make a mind map. \
                The output should be a json format with specific key structure as 'root' and 'children'. \
                The 'root' should be a string and 'children' should be a list of dictionary with each dictionary representing a topic and its list of subtopics. \
                """
            },
            {
                "role": "user", 
                "content": f"""
                <summary>{sample_txt}</summary>
 
                ```{chr(123)}required output json format{chr(125)}
                {chr(123)}"root": "<meeting core topic>", "children": [{chr(123)} "Topic A": ["Sub Topic A1", "Sub Topic A2", ...] {chr(125)}, {chr(123)} "Topic B": ["Sub Topic B1", "Sub Topic B2', ...] {chr(125)} ]
                ```
                """
            },
            {
                "role": "assistant", 
                "content": f"""{chr(123)}"root": "Writing Guidance for the Youth Association\'s Representative", "children": [{chr(123)} "Writing Advice From Zhang Laoshi": ["Coverage of personal growth, social environment, and personal identity", "Emphasis on clarity, brevity, and confidence in writing"] {chr(125)}, {chr(123)} "Discussion Topics": ["Importance of well-being and world connection"] {chr(125)}, {chr(123)} "Association\'s Activities": ["Aimed at gaining deeper understanding"] {chr(125)} ]"""
            },
            {
                "role": "user", 
                "content": f"""
                <summary>{txt}</summary>
 
                ```{chr(123)}required output json format{chr(125)}
                {chr(123)}"root": "<meeting core topic>", "children": [{chr(123)} "Topic A": ["Sub Topic A1", "Sub Topic A2", ...] {chr(125)}, {chr(123)} "Topic B": ["Sub Topic B1", "Sub Topic B2', ...] {chr(125)} ]
                ```
                """
            }
        ],
        engine=openai_config['openai_model_engine'],
        temperature=.1,
        top_p=.5,
        max_tokens=2048,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None,
    )['choices'][0]["message"]["content"]

    return {"txt": txt, "html": html, "mindmap": mindmap}



def get_meeting_minutes(transcript, openai_config):

    openai.api_type = openai_config['openai_api_type']
    openai.api_base = openai_config['openai_api_base']
    openai.api_version = openai_config['openai_api_version']
    openai.api_key = openai_config['openai_api_key']

    txt = openai.ChatCompletion.create(
        messages = [
            {
                "role": "system",
                "content": f"""
                Record meeting minutes from a meeting recording. \
                You are given the transcript of the meeting (delimited with XML tags <transcript></transcript>), and you need to capture the key points discussed. \
                The minutes should be detailed and concise, represented as bullet points. \
                Follow the user expected output format. \
                Respond in English, even if the transcript is in Chinese.
                """,
            },
            {
                "role": "user", 
                "content": f"""
                ```{chr(123)}expected format{chr(125)}
                Meeting Minutes 
                Attendees: <list of attendees>
                
                Agenda:
                <list of agenda items, use numbers to separate>
                
                Meeting Details:
                <follow the format below, summarise the details for each agenda item listed above>
                <number>: <agenda item>
                <list of discussed items>
                
                Action Items:
                <list of follow up actions>

                ```
                 
                <transcript>{transcript}</transcript>
                
                """
            }
        ],
        engine=openai_config['openai_model_engine'],
        temperature=.1,
        top_p=.5,
        max_tokens=2048,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None,
    )['choices'][0]["message"]["content"]
    
    html = openai.ChatCompletion.create(
        messages = [
            {
                "role": "system",
                "content": f"""
                You are given meeting minutes (delimited with XML tags <minutes></minutes>), and you need to convert them into HTML format. \
                Your output should be in the <div> and should only include syntax used in HTML. \
                Which mean you should ignore the <body> since you would be embedded into another parent <div>
                """,
            },
            {
                "role": "user", 
                "content": f"""<minutes><{txt}/minutes>"""
            }
        ],
        engine=openai_config['openai_model_engine'],
        temperature=.1,
        top_p=.5,
        max_tokens=2048,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None,
    )['choices'][0]["message"]["content"]
    
    return {"txt": txt, "html": html}


def get_assistant_response(minutes, query, openai_config, debug=False):

    openai.api_type = openai_config['openai_api_type']
    openai.api_base = openai_config['openai_api_base']
    openai.api_version = openai_config['openai_api_version']
    openai.api_key = openai_config['openai_api_key']

    if debug:
        responses = [
            "Sure, I can help with that.",
            "Could you please provide more information?",
            "I'm sorry, I didn't quite understand. Could you please rephrase that?",
            "Yes, of course.",
            "Let me check that for you."
        ]
        # Randomly select a response
        return random.choice(responses)

    response = openai.ChatCompletion.create(
        messages = [
            {
                "role": "system",
                "content": f"""
                Record meeting minutes from a meeting recording. \
                You are given the minutes of the meeting (delimited with XML tags <minutes></minutes>), and you need to answer any question (delimited with XML tags <question></question>) from user regarding to the minutes. \
                You answer should be concise and like a human-being. \
                Respond in English, even if user ask in Chinese.
                """,
            },
            {
                "role": "user", 
                "content": f"""
                <minutes><{minutes}/minutes>

                <question><{query}/question>
                """
            }
        ],
        engine=openai_config['openai_model_engine'],
        temperature=.1,
        top_p=.5,
        max_tokens=2048,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None,
    )['choices'][0]["message"]["content"]

    return response
