import pickle
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_frequency_file():
    input_file = Path('en_full.txt')  # The manually downloaded file
    output_file = Path('word_frequency.pkl')
    
    if not input_file.exists():
        logger.error(f"Could not find input file: {input_file}")
        logger.error("Please make sure you renamed the downloaded file to 'en_full.txt'")
        return
        
    logger.info("Processing word frequency file...")
    frequencies = {}
    total_lines = 0
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        word, freq = line.split(' ')
                        frequencies[word] = int(freq)
                        total_lines += 1
                        if total_lines % 10000 == 0:
                            logger.info(f"Processed {total_lines:,} words...")
                    except ValueError:
                        logger.warning(f"Skipping malformed line: {line.strip()}")
                        
        logger.info(f"Processing complete. Found {total_lines:,} words.")
        logger.info(f"Saving to {output_file}")
        
        with open(output_file, 'wb') as f:
            pickle.dump(frequencies, f)
            
        logger.info("Done! You can now run the smart review system.")
        
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        return

if __name__ == "__main__":
    process_frequency_file() 