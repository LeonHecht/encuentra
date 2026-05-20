import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from typing import Dict, List, Tuple

class LanguageDetector:
    def __init__(self, ngram_range: Tuple[int, int] = (2, 4)):
        """
        Initializes the Language Detector.
        Uses character n-grams (e.g., 2 to 4 characters) to build the vocabulary.
        """
        self.classes_ = []
        
        # A Pipeline ensures the data transformations and the model are bundled together.
        self.pipeline = Pipeline([
            # TfidfVectorizer automatically handles sparse matrices and tokenizes by character
            ('vectorizer', TfidfVectorizer(
                analyzer='char', 
                ngram_range=ngram_range, 
                lowercase=True,
                max_features=50000 # Prevents memory explosion by capping vocabulary
            )),
            # Logistic Regression optimized for multi-class classification
            ('classifier', LogisticRegression(
                solver='lbfgs', 
                max_iter=500
            ))
        ])

    def train(self, data: Dict[str, List[str]]) -> None:
        """
        Trains the model on a dictionary of {language_label: [texts]}.
        """
        X_train = []
        y_train = []
        
        for lang, texts in data.items():
            X_train.extend(texts)
            y_train.extend([lang] * len(texts))
            
        self.classes_ = list(data.keys())
        
        # The pipeline handles building the vocabulary and fitting the weights
        self.pipeline.fit(X_train, y_train)

    def predict(self, text: str, confidence_threshold: float = 0.4) -> str:
        """
        Predicts the language of a single text string.
        Includes a threshold to handle entirely unseen or nonsensical data.
        """
        # Get the probability distribution across all learned languages
        probabilities = self.pipeline.predict_proba([text])[0]
        max_prob_index = np.argmax(probabilities)
        max_prob = probabilities[max_prob_index]
        
        # If the model is not confident, return "Unknown"
        if max_prob < confidence_threshold:
            return "Unknown"
            
        # Extract the predicted class directly from the pipeline
        return self.pipeline.classes_[max_prob_index]

# --- Example Usage ---
if __name__ == "__main__":
    # 1. Dummy training data
    training_data = {
        "English": [
            "Hello, how are you?", 
            "Software engineering is fascinating.",
            "I love programming in Python.",

        ],
        "German": [
            "Hallo, wie geht es dir?", 
            "Softwareentwicklung ist faszinierend.",
            "Ich liebe es, in Python zu programmieren."
        ],
        "Spanish": [
            "Hola, ¿cómo estás?", 
            "La ingeniería de software es fascinante.",
            "Me encanta programar en Python."
        ]
    }

    # 2. Initialize and train
    detector = LanguageDetector(ngram_range=(2, 4))
    detector.train(training_data)

    # 3. Test predictions
    test_strings = [
        "This is a test of the system.",           # English
        "Das ist ein einfacher Test.",             # German
        "El sistema funciona perfectamente.",      # Spanish
    ]

    for text in test_strings:
        prediction = detector.predict(text, confidence_threshold=0.45)
        print(f"Text: '{text}' -> Predicted: {prediction}")