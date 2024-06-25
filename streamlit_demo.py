import os
import time
import base64
import logging
from mimetypes import guess_type
import streamlit as st
from openai import AzureOpenAI
import openai
from langchain_core.prompts import PromptTemplate
from langchain_openai import AzureChatOpenAI

logging.basicConfig(level=logging.DEBUG)

# Banner Message
def print_banner():
    banner = """
#####
#        ####  #####  ######
#       #    # #    # #
#       #    # #    # #####
#       #    # #    # #
#       #    # #    # #
 #####   ####  #####  ######

 #####
#     # ###### #    # ###### #####    ##   #####  ####  #####
#       #      ##   # #      #    #  #  #    #   #    # #    #
#  #### #####  # #  # #####  #    # #    #   #   #    # #    #
#     # #      #  # # #      #####  ######   #   #    # #####
#     # #      #   ## #      #   #  #    #   #   #    # #   #
 #####  ###### #    # ###### #    # #    #   #    ####  #    #
    """
    st.markdown(f"```\n{banner}\n```")

# Set a longer timeout value (in seconds)
openai.api_request_timeout = 3000  # Set to 300 seconds or as needed

# Function to encode a local image into data URL 
def local_image_to_data_url(image_path):
    mime_type, _ = guess_type(image_path)
    if mime_type is None:
        mime_type = 'application/octet-stream'  # Default MIME type if none is found
    with open(image_path, "rb") as image_file:
        base64_encoded_data = base64.b64encode(image_file.read()).decode('utf-8')
    return f"data:{mime_type};base64,{base64_encoded_data}"

def main():
    st.title("Terraform Code Generator")

    # Display banner and welcome message
    print_banner()
    st.write("Welcome To Terraform Code Generator!")

    # Use Streamlit's session state to manage the state
    if "submitted" not in st.session_state:
        st.session_state.submitted = False
    if "outline_saved" not in st.session_state:
        st.session_state.outline_saved = False

    # Prompt user for image path
    image_path = st.text_input("Enter the image path in jpeg format:")

    if st.button("Submit"):
        if not os.path.isfile(image_path):
            st.error(f"Error: The file '{image_path}' does not exist.")
            return
        st.session_state.submitted = True
        st.session_state.image_path = image_path

    if st.session_state.submitted:
        st.write("Parsing The Architecture diagram...!")

        api_base = os.getenv("AZURE_OPENAI_ENDPOINT")
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        deployment_name = 'gpt-4o-2024-05-13'
        api_version = '2024-02-01'

        client = AzureOpenAI(
            api_key=api_key,  
            api_version=api_version,
            base_url=f"{api_base}/openai/deployments/{deployment_name}"
        )

        data_url = local_image_to_data_url(st.session_state.image_path)

        st.write("Interpreting The Architecture Diagram...!")
        time.sleep(10)

        save_path = st.text_input("Enter The File Path To Save The Outline Prompt:")

        if save_path and st.button("Save Outline Prompt"):
            try:
                logging.debug("Sending request to OpenAI API")
                response = client.chat.completions.create(
                    model=deployment_name,
                    messages=[
                        { "role": "system", "content": "Act as a Prompt Engineer. Help to capture requirements from the diagram. Describe the diagram accurately as outline prompt" },
                        { "role": "user", "content": [
                            { 
                                "type": "text", 
                                "text": (
                                    "Act as a Cloud Architect. Describe the diagram in detail. \n"
                                )
                            },
                            { 
                                "type": "image_url",
                                "image_url": {
                                    "url": data_url
                                }
                            }
                        ] } 
                    ],
                    max_tokens=3500
                )
                logging.debug("Response received from OpenAI API")
            with open(save_path, "w", encoding="utf-8") as file:
                file.write(response.choices[0].message.content)

            st.write(f"Outline Prompt Has Been Generated And Saved To {save_path}")
            st.session_state.outline_saved = True
            st.session_state.outline_path = save_path
        except Exception as e:
                logging.error(f"Error occurred: {e}")
                st.error(f"Failed to generate outline prompt: {e}")

    if st.session_state.outline_saved:
        time.sleep(10)
        st.write("Generating The Terraform Code...!")

        azure_openai_client = AzureChatOpenAI(
            azure_deployment=deployment_name,
            openai_api_version=api_version,
            openai_api_key=api_key
        )

        part1_template = PromptTemplate(
            input_variables=["outline"],
            template="""
            Act as a Terraform expert.Only terraform code. No description. Generate the code for labelled Part 1 only from outline_prompt.No description. Important:- only part 1 code
            Part 1: env\\main - This section should include the cloud provider name, tfvars and config files, and provider.tf to capture provider information for Terraform.
            Ensure no duplication and correct boundaries.
            Outline:
            {outline}
            """
        )

        part2_template = PromptTemplate(
            input_variables=["outline"],
            template="""
            Act as a Terraform expert.Only terraform code. No description. Generate the code for labelled Part  2 only from outline_prompt. No description. Important:- only part 2 code
            Part 2: templates - If any templates are required (e.g., Kubernetes or ArgoCD templates), they should be included here
            Ensure no duplication and correct boundaries.
            Outline:
            {outline}
            """
        )

        part3_template = PromptTemplate(
            input_variables=["outline"],
            template="""
            Act as a Terraform expert.Only terraform code. No description. Generate the code for labelled Part  3 only from outline_prompt. No description. Important:- only part 3 code.
            Part 3: Root main.tf - This will call the modules to implement the code. The resource block should contain all required parameters for the code to succeed. Declare variables and outputs as needed
            Ensure no duplication and correct boundaries.
            Outline:
            {outline}
            """
        )

        part4_template = PromptTemplate(
            input_variables=["outline"],
            template="""
            Act as a Terraform expert.Only terraform code. No description. Generate the code for labelled Part  4 only from outline_prompt. No description. Important:- only part 4 code.
            Part 4: modules - All relevant resources should be segregated into modules for reusability. Declare variables and outputs as required
            Ensure no duplication and correct boundaries.
            Outline:
            {outline}
            """
        )

        part1_sequence = part1_template | azure_openai_client
        part2_sequence = part2_template | azure_openai_client
        part3_sequence = part3_template | azure_openai_client
        part4_sequence = part4_template | azure_openai_client

        def chunk_text(text, max_chunk_length):
            return [text[i:i+max_chunk_length] for i in range(0, len(text), max_chunk_length)]

        def generate_code(sequence, outline_prompt, max_chunk_length):
            chunks = chunk_text(outline_prompt, max_chunk_length)
            code = ""
            for chunk in chunks:
                response = sequence.invoke({"outline": chunk})
                code += response.content
            return code

        with open(st.session_state.outline_path, "r", encoding="utf-8") as file:
            outline_prompt = file.read()

        MAX_CHUNK_LENGTH = 4000

        part1_code = generate_code(part1_sequence, outline_prompt, MAX_CHUNK_LENGTH)
        part2_code = generate_code(part2_sequence, outline_prompt, MAX_CHUNK_LENGTH)
        part3_code = generate_code(part3_sequence, outline_prompt, MAX_CHUNK_LENGTH)
        part4_code = generate_code(part4_sequence, outline_prompt, MAX_CHUNK_LENGTH)

        base_path = "C:/tvh/devops/azure"

        with open(os.path.join(base_path, "part1.tf"), "w", encoding="utf-8") as file:
            file.write(part1_code)

        with open(os.path.join(base_path, "part2.tf"), "w", encoding="utf-8") as file:
            file.write(part2_code)

        with open(os.path.join(base_path, "part3.tf"), "w", encoding="utf-8") as file:
            file.write(part3_code)

        with open(os.path.join(base_path, "part4.tf"), "w", encoding="utf-8") as file:
            file.write(part4_code)

        code_path = st.text_input("Enter The File Path To Save The Terraform Code:")

        if code_path and st.button("Save Terraform Code"):
            time.sleep(5)
            with open(os.path.join(base_path, "part1.tf"), "r", encoding="utf-8") as file:
                output1_content = file.read()

            with open(os.path.join(base_path, "part2.tf"), "r", encoding="utf-8") as file:
                output2_content = file.read()

            with open(os.path.join(base_path, "part3.tf"), "r", encoding="utf-8") as file:
                output3_content = file.read()

            with open(os.path.join(base_path, "part4.tf"), "r", encoding="utf-8") as file:
                output4_content = file.read()

            final_code = output1_content + "\n" + output2_content + "\n" + output3_content +  "\n" + output4_content

            with open(code_path, "w", encoding="utf-8") as final_file:
                final_file.write(final_code)

            st.write(f"Terraform Code Has Been Generated And Saved To {code_path}")

if __name__ == "__main__":
    main()
