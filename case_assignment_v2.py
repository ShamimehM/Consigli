# Importing necessary libraries

import os
import re
import pandas as pd
from PyPDF2 import PdfReader
from openai import OpenAI

# Initialize OpenAI client
# Fetch the OpenAI API key from environment variables for security.
# This assumes the API key is stored in an environment variable named "OPENAI_API_KEY".
api_key = os.getenv("OPENAI_API_KEY")
# Check if the API key is available; if not, warn the user.
if not api_key:
    raise ValueError("OpenAI API key is not set in the environment variables.")

# Create an OpenAI client instance using the provided API key.
client = OpenAI(api_key=api_key)

def read_pdf(file_path):
    """
    Extracts text from a PDF file.
    Input:
        - file_path: The path to the PDF file to be read.
    Output:
        - A single string containing all the extracted text from the PDF.
    """

    # Initializing a PdfReader object to read the PDF at the given file path.
    pdf_reader = PdfReader(file_path)

    # Extracting text from all pages in the PDF and combining it into one string.
    # Then a generator expression will iterate through the pages and extract text.
    return "".join(page.extract_text() for page in pdf_reader.pages)

def split_into_paragraphs(text):
    """
    Split text into paragraphs and handle long paragraphs by breaking them into smaller chunks.
    Input:
        - text: The full text to be split into paragraphs.
    Output:
        - adjusted_paragraphs: A list of paragraphs, with long ones adjusted to smaller sizes.
    """

    # Step 1: Split the text into paragraphs based on blank lines.
    # Uses regular expressions to identify and split on double newlines.
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]

    # Step 2: Analyze paragraph lengths.
    # Calculates the total number of words across all paragraphs.
    total_words = sum(len(p.split()) for p in paragraphs)
    # Determines the number of paragraphs.
    num_paragraphs = len(paragraphs)

    # Calculates the average number of words per paragraph.
    avg_words = total_words / num_paragraphs if num_paragraphs > 0 else 0
    print( "Average words per paragraph: " ,avg_words)

    # Defines a threshold for long paragraphs.
    # A paragraph is considered too long if it exceeds 20% more than the average length.
    length_threshold = avg_words + ((avg_words * 20) /100)
    print("Length threshold:" , length_threshold)

    # Step 3: Adjust paragraphs that exceed the threshold.
    adjusted_paragraphs = []
    for paragraph in paragraphs:
        word_count = len(paragraph.split()) # Calculate the word count of the current paragraph.

        if word_count > length_threshold:
            # If the paragraph is too long, split it into smaller chunks.
            words = paragraph.split()
            start = 0
            while start < len(words):
                adjusted_paragraphs.append(" ".join(words[start:start + int(avg_words)]))
                start += int(avg_words)
        else:
            # If the paragraph length is within the threshold, keep it as is.
            adjusted_paragraphs.append(paragraph)

    return adjusted_paragraphs

def classify_paragraphs(client, paragraphs):
    #Classifying paragraphs into predefined topics w/ GPT.
    # Input:
    #   - client: The client objects to interact with the GPT model.
    #   - paragraphs: A list of text paragraphs to classify.
    # Output:
    #   - topics: A list of topics corresponding to each paragraph.

    topics = []  # Initializes an empty list to store classification results.

    for paragraph in paragraphs:
        try: # Generates a GPT-based classification for the current paragraph.
            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                store=True, # The interaction should be stored.
                messages=[
                    {
                        "role": "user",
                        "content": (
                            "You're a helpful assistant. Classify the following text into one of these topics: "
                            "Politics, Sports, Economics, Entertainment.\n\n"
                            f"Text: {paragraph}\n\nTopic:"
                        )
                    }
                ]
            )
            # Extracts the classified topic from the GPT response.
            topic = completion.choices[0].message.content.strip()
            topics.append(topic) # Adds the topic to the list.
        except Exception as e:
            # Handle errors
            topics.append("Error") # adds "Error" if something is wrong.
            print(f"Error processing paragraph: {e}")
    return topics

def main():
    #The main function is to process PDF and classify content.
    # Determine the file path depending on the environment (Google Colab or local machine).
    file_path = "/content/news.pdf" if os.path.exists('/content') else "news.pdf"

    # Step 1: Read the PDF file
    try:
        pdf_text = read_pdf(file_path) # Reads the content of the PDF file at the specified path.
    except Exception as e:
        # Will print an error message and terminate the function if reading fails.
        print(f"Failed to read the PDF: {e}")
        return

    # Step 2: Split the content into paragraphs
    paragraphs = split_into_paragraphs(pdf_text)
    if not paragraphs:
        print("No paragraphs found in the document.") # Notify and terminate if no paragraphs are found.
        return

    # Step 3: Classify each paragraph using GPT
    topics = classify_paragraphs(client, paragraphs)

    # Step 4: Store the results in a DataFrame
    df = pd.DataFrame({"news": paragraphs, "topics": topics})
    # Combine paragraphs and their classified topics into a Pandas DataFrame.


    # Step 5: Save the results to a CSV file
    # Define the output path based on the environment (Colab or local machine).
    output_path = "/content/classified_news.csv" if os.path.exists('/content') else "classified_news.csv"
    try:
        df.to_csv(output_path, index=False)
        print(f"Classified results saved to '{output_path}'.")
    except Exception as e:
        print(f"Failed to save the results: {e}") # Will print an error message if saving fails.

if __name__ == "__main__":
    main()
