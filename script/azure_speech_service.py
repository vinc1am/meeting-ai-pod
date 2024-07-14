import logging
import sys
import requests
import time
import swagger_client
import json
import random


def whisper_transcribe_from_url(client, url, properties, model_reference):

    model = {'self': f'{client.configuration.host}/models/{model_reference}'}
    transcription_definition = swagger_client.Transcription(
        display_name="meeting_audio_transcription",
        description="meeting_audio_transcription",
        locale="zh-HK",
        content_urls=[url],
        model=model,
        properties=properties
    )
    return transcription_definition

def _paginate(api, paginated_object):

    yield from paginated_object.values
    typename = type(paginated_object).__name__
    auth_settings = ["api_key"]
    while paginated_object.next_link:
        link = paginated_object.next_link[len(api.api_client.configuration.host):]
        paginated_object, status, headers = api.api_client.call_api(link, "GET",
            response_type=typename, auth_settings=auth_settings)

        if status == 200:
            yield from paginated_object.values
        else:
            raise Exception(f"could not receive paginated data: status {status}")

def transcribe(recordings_blob_uri, model_reference, subscription_key, service_region, debug=False):
    if debug:
        def generate_fake_transcription(minutes=10):
            fake_transcription_list = []
            
            phrases = [
                ['Hello, how is everyone doing today ?', 'I am doing good, thank you.', 'Same here.', 'Great, let us start the meeting.'],
                ['We are here to discuss the project milestone delivery.', 'The first point on the agenda is about budget.'],
                ['We are over budget for the project.', 'We need to look at the areas causing budget overflow.', 'One of the reasons is high infrastructure cost.'],
                ['Let\'s move to the second point about timeline.', 'There is a delay due to unforeseen issues. We are formulating a plan to address it.'],
                ['The third point is about resources.', 'We need two more team members to meet the deadline.', 'I propose we get freelancers for this job.'],
                ['Next point is about the risk management.', 'We have identified potential risks such as a further increase in infrastructure cost, and delay in delivery.'],
                ['The last point is about stakeholders communication.', 'We need to inform stakeholders about the revised budget and timeline.', 'I agree. Informed stakeholders can provide useful suggestions.'],
                ['Great discussion! Let\'s wrap up and follow the actions discussed.']
            ]
            
            total_phrases = len(phrases)
            
            for minute in range(0, total_phrases):
                for i, phrase in enumerate(phrases[minute]):
                    speaker = i % 2 + 1
                    timestamp_in_seconds = minute * 60 + (i % 2)*30  # Every 30 sec each speaker
                    fake_transcription_list.append({
                        'speaker': f'Speaker {speaker}',
                        'display': phrase,
                        'timestamp_in_seconds': timestamp_in_seconds
                    })

            return fake_transcription_list

        return generate_fake_transcription(10) 

    logging.info("Starting transcription client...")

    # configure API key authorization: subscription_key
    configuration = swagger_client.Configuration()
    configuration.api_key["Ocp-Apim-Subscription-Key"] = subscription_key
    configuration.host = f"https://{service_region}.api.cognitive.microsoft.com/speechtotext/v3.1"

    # create the client object and authenticate
    client = swagger_client.ApiClient(configuration)

    # create an instance of the transcription api class
    api = swagger_client.CustomSpeechTranscriptionsApi(api_client=client)

    properties = swagger_client.TranscriptionProperties()
    properties.display_form_word_level_timestamps_enabled = True
    properties.punctuation_mode = "DictatedAndAutomatic"
    properties.profanity_filter_mode = "None"
    # properties.destination_container_url = transcripts_container_uri
    properties.time_to_live = "PT1H"
    properties.diarization_enabled = True
    properties.diarization = swagger_client.DiarizationProperties(
        swagger_client.DiarizationSpeakersProperties(min_count=1, max_count=10))
    
    properties.language_identification = swagger_client.LanguageIdentificationProperties(["zh-HK", "en-US", "zh-CN"])

    transcription_definition = whisper_transcribe_from_url(client, recordings_blob_uri, properties, model_reference)
    
    created_transcription, status, headers = api.transcriptions_create_with_http_info(transcription=transcription_definition)

    # get the transcription Id from the location URI
    transcription_id = headers["location"].split("/")[-1]

    completed = False

    results = None

    while not completed:
        # wait for 5 seconds before refreshing the transcription status
        time.sleep(10)

        transcription = api.transcriptions_get(transcription_id)
        logging.info(f"Transcriptions status: {transcription.status}")

        if transcription.status in ("Failed", "Succeeded"):
            completed = True

        if transcription.status == "Succeeded":
            pag_files = api.transcriptions_list_files(transcription_id)
            for file_data in _paginate(api, pag_files):
                if file_data.kind != "Transcription":
                    continue

                audiofilename = file_data.name
                results_url = file_data.links.content_url
                results = requests.get(results_url)
        elif transcription.status == "Failed":
            print(f"Transcription failed: {transcription.properties.error.message}")
            if results is not None: 
                print(results.content) 

    print(results.content)
    print(results.content.decode('utf-8'))
    results = json.loads(results.content.decode('utf-8'))

    transcription_list = []
    last_speaker = None
    current_phrase = ""
    current_timestamp = None

    # Consolidate into a dictionary
    for data in results['recognizedPhrases']:
        current_speaker = data['speaker']
        display_text = data['nBest'][0]['display']

        # Convert offset in ticks to seconds 
        timestamp_in_seconds = data['offsetInTicks'] / 10000000

        if current_speaker != last_speaker:
            # If the last_speaker was not None, we store the previous speaker's phrases
            if last_speaker is not None:
                transcription_list.append({
                'speaker': last_speaker,
                'display': current_phrase,
                'timestamp_in_seconds': current_timestamp
                })

            # Set current_phrase to the new speaker's phrase and store the timestamp
            current_phrase = display_text
            current_timestamp = timestamp_in_seconds
        else:
            # If the same speaker continues speaking, add up the phrases
            current_phrase += " " + display_text

        last_speaker = current_speaker
    
    # Append the last phrase
    if current_phrase:  
        transcription_list.append({
        'speaker': last_speaker,
        'display': current_phrase,
        'timestamp_in_seconds': current_timestamp
        })

    return transcription_list





def simplify_transcript(transcription_list):

    simplified_transcription = []
    for transcription in transcription_list:
        simplified_transcription.append()

