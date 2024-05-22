import pandas as pd
from bs4 import BeautifulSoup
import requests
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
import re


# Download necessary NLTK resources
nltk.download('punkt')

# Load the Excel file
input_file = 'Input.xlsx'
df = pd.read_excel(input_file)

# Retrieving URLs and URL_IDs
urls = df.iloc[:, 1].tolist()
url_ids= df.iloc[:, 0].tolist()

# Function to extract text from a URL
def extract_text(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Extract title and text based on common HTML tags; adjust as needed
    title = soup.find('h1').get_text(strip=True)
    article_text = ' '.join([p.get_text(strip=True) for p in soup.find_all('p')])
    
    return title, article_text

# Function to load custom stop words from multiple files
def load_stop_words():
    stop_words = set()
    # List all your stop words files
    stop_words_files = ['StopWords_Auditor.txt', 'StopWords_Currencies.txt', 'StopWords_DatesandNumbers.txt', 'StopWords_Generic.txt', 'StopWords_GenericLong.txt', 'StopWords_Geographic.txt', 'StopWords_Names.txt']
    for file_name in stop_words_files:
        with open(file_name, 'rb') as file:
            stop_words.update(word.strip().lower() for word in file.readlines())
    return stop_words

# Load stop words
stop_words = load_stop_words()

# Function to clean and process text
def clean_text(text):
    # Tokenize text
    words = word_tokenize(text)
    # Remove stop words and punctuation
    words = [word.lower() for word in words if word.isalpha() and word not in stop_words]
    return words

# Function to load words from a file
def load_words(file_path):
    with open(file_path, 'r') as file:
        words = [line.strip().lower() for line in file.readlines()]
    return words

# Load positive and negative words
positive_words = load_words('positive-words.txt')
negative_words = load_words('negative-words.txt')

# Function to count syllables in a word
def syllable_count(word):
    word = word.lower()
    syllables = 0
    vowels = "aeiouy"
    if word[0] in vowels:
        syllables += 1
    for index in range(1, len(word)):
        if word[index] in vowels and word[index - 1] not in vowels:
            syllables += 1
    if word.endswith("es") or word.endswith("ed"):
        syllables -= 1
    if syllables == 0:
        syllables = 1
    return syllables

# Function to calculate sentiment scores
def calculate_sentiment_scores(words):
    positive_score = sum(1 for word in words if word in positive_words)
    negative_score = sum(1 for word in words if word in negative_words)
    total_words = len(words)
    polarity_score = (positive_score - negative_score) / ((positive_score + negative_score) + 0.000001)
    subjectivity_score = (positive_score + negative_score) / (total_words + 0.000001)
    return positive_score, negative_score, polarity_score, subjectivity_score

# Function to calculate readability metrics
def calculate_readability(text, words):
    sentences = sent_tokenize(text)
    total_sentences = len(sentences)
    total_words = len(words)
    average_sentence_length = total_words / total_sentences if total_sentences > 0 else 0
    complex_words = sum(1 for word in words if syllable_count(word) > 2)
    percentage_complex_words = (complex_words / total_words) * 100 if total_words > 0 else 0
    fog_index = 0.4 * (average_sentence_length + percentage_complex_words)
    syllables_per_word = sum(syllable_count(word) for word in words) / total_words if total_words > 0 else 0
    return {
        'average_sentence_length': average_sentence_length,
        'percentage_complex_words': percentage_complex_words,
        'fog_index': fog_index,
        'complex_word_count': complex_words,
        'total_word_count': total_words,
        'syllables_per_word': syllables_per_word
    }

# Function to count personal pronouns in text
def count_personal_pronouns(text):
    pronouns = re.findall(r'\b(I|we|my|ours|us)\b', text, re.IGNORECASE)
    return len(pronouns)

# Function to calculate average word length
def average_word_length(words):
    total_length = sum(len(word) for word in words)
    return total_length / len(words) if words else 0

# Dictionary to hold extracted data
articles = {}

# List to hold cleaned data
articles_cln = []

for url, url_id in zip(urls, url_ids):
    response = requests.get(url)
    if response.status_code == 200:
        title, text = extract_text(url)
        articles[url_id] = {'url': url, 'title': title, 'text': text}
        words = clean_text(text)
        positive_score, negative_score, polarity_score, subjectivity_score = calculate_sentiment_scores(words)
        readability_metrics = calculate_readability(text, words)
        personal_pronouns = count_personal_pronouns(text)
        avg_word_length = average_word_length(words)
        articles_cln.append({
            'URL_ID': url_id, 'URL': url,
            'POSIIVE_SCORE': positive_score, 'NEGATIVE_SCORE': negative_score,
            'POLARITY_SCORE': polarity_score, 'SUBJECTIVITY_SCORE': subjectivity_score,
            'AVERAGE_SENTENCE_LENGTH': readability_metrics['average_sentence_length'], 'PERCENTAGE_OF_COMPLEX_WORDS': readability_metrics['percentage_complex_words'],
            'FOG_INDEX': readability_metrics['fog_index'], 'COMPLEX_WORD_COUNT': readability_metrics['complex_word_count'],
            'WORD_COUNT': readability_metrics['total_word_count'],
            'SYLLABLE_PER_WORD': readability_metrics['syllables_per_word'],
            'PERSONAL_PRONOUNS': personal_pronouns, 'AVERAGE_WORD_LENGTH': avg_word_length})
                             
    
# Save articles to individual text files        
for url_id, article in articles.items():
    with open(f'{url_id}.txt', 'w', encoding='utf-8') as file:
        file.write(article['title'] + '\n' + article['text'])

        
# Convert list of dictionaries to a DataFrame
articles_cln_df = pd.DataFrame(articles_cln)

# Save to CSV
articles_cln_df.to_csv('cleaned_articles.csv', index=False)