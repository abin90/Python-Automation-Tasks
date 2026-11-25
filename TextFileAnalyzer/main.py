import os
import re
import csv

from collections import Counter


# ---------------------------------------
# STEP 1: Define Folder Paths
# ---------------------------------------

input_folder = "feedback_files"
output_folder = "reports"

output_file = os.path.join(output_folder, "analysis_report.csv")


# ---------------------------------------
# STEP 2: Common Words to Ignore
# ---------------------------------------

stop_words = {
    "the", "is", "and", "a", "an",
    "to", "of", "in", "for", "on",
    "with", "was", "were", "are",
    "this", "that", "it", "we",
    "i", "you", "he", "she", "they",
    "my", "our", "your", "at", "but",
    "as", "be", "have", "has", "had"
}


# ---------------------------------------
# STEP 3: Create Output Folder
# ---------------------------------------

os.makedirs(output_folder, exist_ok=True)


# ---------------------------------------
# STEP 4: Create Lists to Store Results
# ---------------------------------------

report_data = []

all_words = []

all_bigrams = []


# ---------------------------------------
# STEP 5: Read All Text Files
# ---------------------------------------

for filename in os.listdir(input_folder):

    if filename.endswith(".txt"):

        file_path = os.path.join(input_folder, filename)

        with open(file_path, "r", encoding="utf-8") as file:

            content = file.read()


            # ---------------------------------------
            # STEP 6: Calculate Basic Statistics
            # ---------------------------------------

            total_characters = len(content)

            total_lines = len(content.splitlines())


            # ---------------------------------------
            # STEP 7: Tokenization
            # ---------------------------------------

            words = re.findall(r"\b[a-zA-Z0-9']+\b", content.lower())

            total_words = len(words)


            # ---------------------------------------
            # STEP 8: Remove Common Words
            # ---------------------------------------

            filtered_words = [
                word for word in words
                if word not in stop_words
            ]


            # ---------------------------------------
            # STEP 9: Store Words
            # ---------------------------------------

            all_words.extend(filtered_words)


            # ---------------------------------------
            # STEP 10: Generate Bigrams
            # ---------------------------------------

            bigrams = zip(filtered_words, filtered_words[1:])

            all_bigrams.extend(bigrams)


            # ---------------------------------------
            # STEP 11: Store File Statistics
            # ---------------------------------------

            report_data.append({

                "File": filename,

                "Words": total_words,

                "Lines": total_lines,

                "Characters": total_characters

            })


# ---------------------------------------
# STEP 12: Find Most Frequent Words
# ---------------------------------------

word_frequency = Counter(all_words)

most_common_words = word_frequency.most_common(10)


print("\n========== MOST FREQUENT WORDS ==========")

for word, count in most_common_words:

    print(f"{word}: {count}")


# ---------------------------------------
# STEP 13: Find Most Frequent Bigrams
# ---------------------------------------

bigram_frequency = Counter(all_bigrams)

most_common_bigrams = bigram_frequency.most_common(10)


print("\n========== MOST FREQUENT BIGRAMS ==========")

for bigram, count in most_common_bigrams:

    print(f"{bigram[0]} {bigram[1]}: {count}")


# ---------------------------------------
# STEP 14: Generate CSV Report
# ---------------------------------------

with open(output_file, "w", newline="", encoding="utf-8") as csvfile:

    fieldnames = ["File", "Words", "Lines", "Characters"]

    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    writer.writeheader()

    writer.writerows(report_data)


# ---------------------------------------
# STEP 15: Display Final Message
# ---------------------------------------

print("\n===================================")

print("Text File Analysis Completed!")

print("CSV Report Saved Successfully.")

print(f"Report Location: {output_file}")

print("===================================")