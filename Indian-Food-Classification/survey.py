# SMART SPOON ANALYSIS WITH CLEAR VISUALIZATIONS AND SIMPLE REPORTING
import pandas as pd
import mysql.connector
import matplotlib.pyplot as plt
import seaborn as sns
from textblob import TextBlob
from wordcloud import WordCloud
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import LatentDirichletAllocation
import numpy as np
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import re
from datetime import datetime
import warnings
import os

# Configuration
warnings.filterwarnings("ignore")
pd.set_option('display.max_columns', None)
sns.set_style("whitegrid")
plt.rcParams['figure.facecolor'] = 'white'
plt.rcParams['axes.facecolor'] = 'white'

# Database configuration
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "smartspoon_survey"
}

# Excel file path - CHANGE THIS TO YOUR ACTUAL FILE PATH
EXCEL_FILE_PATH = r'smartspoon_survey_data.xlsx'

# ----------------------------
# DATABASE FUNCTIONS
# ----------------------------

def create_database_and_table():
    """Create database and table if they don't exist"""
    try:
        conn = mysql.connector.connect(
            host=DB_CONFIG["host"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"]
        )
        cursor = conn.cursor()
        
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
        print(f"Database '{DB_CONFIG['database']}' created or already exists")
        
        cursor.execute(f"USE {DB_CONFIG['database']}")
        
        create_table_query = """
        CREATE TABLE IF NOT EXISTS survey_responses (
            age INT,
            gender VARCHAR(20),
            follows_low_sodium_diet VARCHAR(10),
            medical_condition VARCHAR(50),
            dining_frequency VARCHAR(20),
            satisfaction_with_low_sodium_food VARCHAR(20),
            adds_salt_condiments VARCHAR(20),
            aware_of_enhancement_tech VARCHAR(10),
            interest_in_smart_spoon VARCHAR(10),
            importance_of_taste_enhancement VARCHAR(30),
            expected_features TEXT,
            consider_purchase VARCHAR(10),
            concerns_about_technology TEXT,
            suggestions_feedback TEXT,
            salt_dal_gojju_palya VARCHAR(20),
            salt_sambar_rasam_curd VARCHAR(20),
            salt_biryani_pulao VARCHAR(20),
            salt_curries VARCHAR(20),
            salt_snacks VARCHAR(20),
            salt_roti_paratha VARCHAR(20),
            salt_pickles VARCHAR(20),
            salt_content_perception VARCHAR(20),
            analysis_remarks TEXT
        )
        """
        cursor.execute(create_table_query)
        print("Table 'survey_responses' created with all columns")
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error creating database/table: {str(e)}")
        return False

def check_existing_data():
    """Check if data already exists in database"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM survey_responses")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return count > 0
    except Exception as e:
        print(f"Error checking existing data: {str(e)}")
        return False

def get_db_connection():
    """Get database connection"""
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Exception as e:
        print(f"Database connection error: {str(e)}")
        return None

def load_and_prepare_data():
    """Load Excel data and prepare for database insertion"""
    try:
        print(f"Looking for data file at: {EXCEL_FILE_PATH}")
        
        # Check if file exists
        if not os.path.exists(EXCEL_FILE_PATH):
            print(f"Error: File not found at {EXCEL_FILE_PATH}")
            print("Please make sure:")
            print("1. The Excel file exists in the same folder as this script")
            print("2. The filename is exactly 'smartspoon_survey_data.xlsx'")
            print("3. Or update the EXCEL_FILE_PATH variable in the code")
            return None
            
        df = pd.read_excel(EXCEL_FILE_PATH)
        df = df.where(pd.notnull(df), None)
        print(f"Successfully loaded {len(df)} records with {len(df.columns)} columns")
        return df
    except Exception as e:
        print(f"Error loading Excel file: {str(e)}")
        return None

def insert_data_to_database(df):
    """Insert data from DataFrame to MySQL database"""
    if df is None:
        print("No data to insert")
        return False
        
    if check_existing_data():
        print("Data already exists in database. Skipping insertion.")
        return True
        
    try:
        conn = get_db_connection()
        if conn is None:
            return False
            
        cursor = conn.cursor()
        
        columns = [
            'age', 'gender', 'follows_low_sodium_diet', 'medical_condition',
            'dining_frequency', 'satisfaction_with_low_sodium_food',
            'adds_salt_condiments', 'aware_of_enhancement_tech',
            'interest_in_smart_spoon', 'importance_of_taste_enhancement',
            'expected_features', 'consider_purchase', 'concerns_about_technology',
            'suggestions_feedback', 'salt_dal_gojju_palya', 'salt_sambar_rasam_curd',
            'salt_biryani_pulao', 'salt_curries', 'salt_snacks', 'salt_roti_paratha',
            'salt_pickles', 'salt_content_perception', 'analysis_remarks'
        ]
        
        # Check if all columns exist in the DataFrame
        missing_cols = [col for col in columns if col not in df.columns]
        if missing_cols:
            print(f"Warning: Missing columns in Excel file: {missing_cols}")
            columns = [col for col in columns if col in df.columns]
        
        df = df[columns]
        placeholders = ', '.join(['%s'] * len(columns))
        query = f"INSERT INTO survey_responses ({', '.join(columns)}) VALUES ({placeholders})"
        data = [tuple(x) for x in df.values]
        
        cursor.executemany(query, data)
        conn.commit()
        print(f"Successfully inserted {len(df)} records into the database")
        return True
        
    except Exception as e:
        print(f"Error inserting data: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# ----------------------------
# IMPROVED ANALYSIS FUNCTIONS
# ----------------------------

def clean_satisfaction_data(value):
    """Clean satisfaction data by converting to numeric"""
    if pd.isna(value):
        return np.nan
    value = str(value).strip().lower()
    if value in ['no', 'sometimes']:
        return 0
    elif value == 'yes':
        return 1
    return np.nan

def analyze_feedback_nlp():
    """Process feedback with clearer visualization"""
    print("\n[POINT 1] Processing feedback with NLP...")
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        feedback = pd.read_sql("SELECT suggestions_feedback FROM survey_responses WHERE suggestions_feedback IS NOT NULL AND suggestions_feedback != ''", conn)
        
        if len(feedback) == 0:
            print("No valid feedback found for analysis")
            return None
        
        nltk.download('vader_lexicon', quiet=True)
        sia = SentimentIntensityAnalyzer()
        
        def get_sentiment(text):
            try:
                scores = sia.polarity_scores(str(text))
                if scores['compound'] >= 0.05: return 'positive'
                elif scores['compound'] <= -0.05: return 'negative'
                return 'neutral'
            except:
                return 'neutral'
        
        feedback['sentiment'] = feedback['suggestions_feedback'].apply(get_sentiment)
        
        # Ensure all sentiment categories exist even if count is zero
        sentiment_counts = feedback['sentiment'].value_counts().reindex(['positive', 'neutral', 'negative'], fill_value=0)
        
        # Improved sentiment visualization with better colors
        plt.figure(figsize=(10, 6))
        
        labels = {
            'positive': 'Happy 😊',
            'neutral': 'Neutral 😐', 
            'negative': 'Concerns 😟'
        }
        
        simple_counts = {labels[k]: v for k,v in sentiment_counts.items()}
        colors = ['#4CAF50', '#FFC107', '#F44336']  # Green, Yellow, Red
        bars = plt.bar(simple_counts.keys(), simple_counts.values(), 
                       color=colors, width=0.6)
        
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height} people',
                    ha='center', va='bottom', fontsize=10)
        
        plt.title('How People Feel About Smart Spoon', pad=20, fontsize=14)
        plt.ylabel('Number of People')
        plt.ylim(0, max(sentiment_counts)*1.1)
        plt.xticks(fontsize=10)
        plt.tight_layout()
        plt.savefig('customer_sentiment.png', dpi=300)
        plt.close()
        
        # Word cloud
        text = ' '.join([str(t) for t in feedback['suggestions_feedback'] if pd.notna(t)])
        if text.strip():
            wordcloud = WordCloud(width=800, height=400, 
                                background_color='white',
                                colormap='viridis').generate(text)
            plt.figure(figsize=(12, 6))
            plt.imshow(wordcloud, interpolation='bilinear')
            plt.axis('off')
            plt.title('Most Common Words in Feedback', fontsize=14)
            plt.savefig('feedback_wordcloud.png', bbox_inches='tight')
            plt.close()
        
        samples = {}
        for sentiment in ['positive', 'neutral', 'negative']:
            subset = feedback[feedback['sentiment'] == sentiment]
            if len(subset) > 0:
                samples[sentiment] = subset.sample(min(3, len(subset)))['suggestions_feedback'].tolist()
            else:
                samples[sentiment] = ["No examples found"]
        
        return {
            'sentiment_counts': sentiment_counts.to_dict(),
            'total_feedback': len(feedback),
            'samples': samples
        }
        
    except Exception as e:
        print(f"Error in NLP analysis: {str(e)}")
        return None
    finally:
        conn.close()

def analyze_satisfaction_patterns():
    """Detect satisfaction patterns with clearer visualization"""
    print("\n[POINT 2] Analyzing satisfaction patterns...")
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        data = pd.read_sql("""
            SELECT age, satisfaction_with_low_sodium_food, 
                   follows_low_sodium_diet, interest_in_smart_spoon,
                   adds_salt_condiments
            FROM survey_responses
            WHERE satisfaction_with_low_sodium_food IS NOT NULL
        """, conn)
        
        if len(data) == 0:
            print("No satisfaction data available for analysis")
            return None
        
        data['satisfaction_numeric'] = data['satisfaction_with_low_sodium_food'].apply(clean_satisfaction_data)
        data = data.dropna(subset=['satisfaction_numeric'])
        
        # Improved visualization
        plt.figure(figsize=(12, 6))
        
        # Convert to simple labels
        data['diet_type'] = data['follows_low_sodium_diet'].map({
            'Yes': 'Low-Salt Diet',
            'No': 'Normal Diet'
        })
        
        sns.boxplot(x='satisfaction_numeric', y='age', hue='diet_type',
                   data=data, palette='Set2')
        
        plt.title('Satisfaction by Age and Diet Type', pad=20)
        plt.xlabel('Satisfaction (0 = Not Satisfied, 1 = Satisfied)')
        plt.ylabel('Age')
        plt.legend(title='Diet Type')
        plt.xticks([0, 1], ['Not Satisfied', 'Satisfied'])
        plt.tight_layout()
        plt.savefig('satisfaction_by_age.png', dpi=300)
        plt.close()
        
        adaptation = data.groupby(['follows_low_sodium_diet', 'adds_salt_condiments'])['interest_in_smart_spoon'].value_counts(normalize=True)
        
        try:
            age_corr = data[['age', 'satisfaction_numeric']].corr().iloc[0,1]
        except:
            age_corr = 0
        
        return {
            'avg_satisfaction': data['satisfaction_numeric'].mean(),
            'diet_impact': data.groupby('follows_low_sodium_diet')['satisfaction_numeric'].mean().to_dict(),
            'age_correlation': age_corr,
            'adaptation_patterns': adaptation.unstack().to_dict('index') if not adaptation.empty else {}
        }
        
    except Exception as e:
        print(f"Error in satisfaction analysis: {str(e)}")
        return None
    finally:
        conn.close()

def predict_improvements():
    """Predict improvements with simpler visualization"""
    print("\n[POINT 3] Predicting improvements...")
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        feedback = pd.read_sql("""
            SELECT suggestions_feedback, concerns_about_technology 
            FROM survey_responses 
            WHERE suggestions_feedback IS NOT NULL AND suggestions_feedback != ''
        """, conn)
        
        if len(feedback) == 0:
            print("No feedback available for improvement prediction")
            return None
        
        feedback['combined'] = feedback['suggestions_feedback'].astype(str) + " " + \
                              feedback['concerns_about_technology'].astype(str)
        
        def clean_text(text):
            text = re.sub(r'[^\w\s]', '', text.lower())
            return text
        
        feedback['cleaned'] = feedback['combined'].apply(clean_text)
        
        vectorizer = TfidfVectorizer(max_features=500, stop_words='english')
        X = vectorizer.fit_transform(feedback['cleaned'])
        
        lda = LatentDirichletAllocation(n_components=3, random_state=42)
        lda.fit(X)
        
        feature_names = vectorizer.get_feature_names_out()
        topics = []
        for i, topic in enumerate(lda.components_):
            top_words = [feature_names[j] for j in topic.argsort()[:-6:-1]]
            sample_idx = np.argmax(lda.transform(X)[:, i])
            topics.append({
                'topic_num': i+1,
                'top_words': top_words,
                'sample_feedback': feedback.iloc[sample_idx]['combined']
            })
        
        # SIMPLER improvement visualization - Pie chart
        plt.figure(figsize=(10, 6))
        
        # Count how many times each topic appears as the dominant topic
        topic_dist = np.argmax(lda.transform(X), axis=1)
        topic_counts = np.bincount(topic_dist)
        
        labels = ["Better Taste", "Lower Price", "Health Features"]
        colors = ['#66b3ff','#99ff99','#ff9999']
        
        plt.pie(topic_counts, labels=labels, colors=colors, autopct='%1.1f%%',
                startangle=90, pctdistance=0.85, textprops={'fontsize': 12})
        
        # Draw circle to make it look like a donut
        centre_circle = plt.Circle((0,0),0.70,fc='white')
        fig = plt.gcf()
        fig.gca().add_artist(centre_circle)
        
        plt.title('What People Want Improved Most', pad=20, fontsize=14)
        plt.tight_layout()
        plt.savefig('improvement_areas.png', bbox_inches='tight', dpi=300)
        plt.close()
        
        return {
            'topics': topics,
            'num_responses': len(feedback),
            'topic_counts': {labels[i]: count for i, count in enumerate(topic_counts)}
        }
        
    except Exception as e:
        print(f"Error in improvement prediction: {str(e)}")
        return None
    finally:
        conn.close()

def analyze_usage_data():
    """Analyze usage data with clearer visualization"""
    print("\n[POINT 4] Analyzing usage data...")
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        data = pd.read_sql("""
            SELECT salt_dal_gojju_palya, salt_sambar_rasam_curd,
                   salt_curries, salt_snacks, salt_content_perception
            FROM survey_responses
        """, conn)
        
        if len(data) == 0:
            print("No usage data available for analysis")
            return None
        
        # Improved visualization
        melted = data.melt(var_name='food', value_name='salt_level')
        
        # Simplify food names
        food_names = {
            'salt_dal_gojju_palya': 'Dal/Curries',
            'salt_sambar_rasam_curd': 'Sambar/Rasam',
            'salt_curries': 'Other Curries',
            'salt_snacks': 'Snacks'
        }
        
        melted['food'] = melted['food'].map(food_names)
        melted = melted.dropna()
        
        plt.figure(figsize=(12, 6))
        sns.countplot(x='food', hue='salt_level', data=melted, palette='coolwarm')
        
        plt.title('Salt Levels in Different Foods', pad=20)
        plt.xlabel('Food Type')
        plt.ylabel('Number of Responses')
        plt.xticks(rotation=45, ha='right')
        plt.legend(title='Reported Salt Level')
        plt.tight_layout()
        plt.savefig('food_salt_levels.png', dpi=300)
        plt.close()
        
        salt_stats = {}
        for col in data.columns[:-1]:
            salt_stats[col] = data[col].value_counts(normalize=True).to_dict()
        
        perception_stats = data['salt_content_perception'].value_counts(normalize=True).to_dict()
        
        return {
            'salt_stats': salt_stats,
            'perception_stats': perception_stats,
            'most_salty': max(salt_stats.items(), key=lambda x: x[1].get('Too High', 0))[0],
            'least_salty': max(salt_stats.items(), key=lambda x: x[1].get('Too Low', 0))[0]
        }
        
    except Exception as e:
        print(f"Error in usage analysis: {str(e)}")
        return None
    finally:
        conn.close()

def evaluate_diet_impact():
    """Evaluate diet impact with clearer visualization"""
    print("\n[POINT 5] Evaluating diet impact...")
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        data = pd.read_sql("""
            SELECT follows_low_sodium_diet, medical_condition,
                   interest_in_smart_spoon, consider_purchase
            FROM survey_responses
        """, conn)
        
        if len(data) == 0:
            print("No diet impact data available for analysis")
            return None
        
        # Improved visualization
        data['diet_type'] = data['follows_low_sodium_diet'].map({
            'Yes': 'Low-Salt Diet',
            'No': 'Normal Diet'
        })
        
        plt.figure(figsize=(10, 6))
        sns.countplot(x='diet_type', hue='consider_purchase',
                     data=data, palette='Set2')
        
        plt.title('Purchase Interest by Diet Type', pad=20)
        plt.xlabel('Diet Type')
        plt.ylabel('Number of Responses')
        plt.legend(title='Would Consider Purchase?')
        plt.tight_layout()
        plt.savefig('diet_impact.png', dpi=300)
        plt.close()
        
        top_conditions = data['medical_condition'].value_counts().head(5).to_dict()
        
        interest_rates = data.groupby('follows_low_sodium_diet')['interest_in_smart_spoon'].value_counts(normalize=True)
        interest_rates = interest_rates.unstack().to_dict('index') if not interest_rates.empty else {}
        
        return {
            'interest_rates': interest_rates,
            'top_conditions': top_conditions,
            'purchase_ratio': data['consider_purchase'].value_counts(normalize=True).to_dict()
        }
        
    except Exception as e:
        print(f"Error in diet impact analysis: {str(e)}")
        return None
    finally:
        conn.close()

# ----------------------------
# SUPER SIMPLE REPORT GENERATION
# ----------------------------

def generate_text_report(results, filename="Simple_SmartSpoon_Report.txt"):
    """Generate very simple report that even a child can understand"""
    print(f"\nGenerating super simple report: {filename}")
    
    # Get total responses count safely
    try:
        df = load_and_prepare_data()
        total_responses = len(df) if df is not None else "Unknown"
    except:
        total_responses = "Unknown"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("="*60 + "\n")
        f.write("SMART SPOON SIMPLE REPORT (EASY TO UNDERSTAND)\n")
        f.write("="*60 + "\n\n")
        f.write(f"Report Date: {datetime.now().strftime('%Y-%m-%d')}\n")
        f.write(f"Total People Surveyed: {total_responses}\n\n")
        
        if total_responses == "Unknown":
            f.write("NOTE: Could not load survey data. Some results may be missing.\n\n")
        
        # 1. What People Think
        if results.get('nlp'):
            nlp_data = results['nlp']
            f.write("1. WHAT PEOPLE THINK ABOUT SMART SPOON\n")
            f.write("-"*60 + "\n")
            f.write(f"Out of {nlp_data['total_feedback']} people who gave feedback:\n")
            
            # Initialize counts with 0 if key doesn't exist
            happy = nlp_data['sentiment_counts'].get('positive', 0)
            neutral = nlp_data['sentiment_counts'].get('neutral', 0)
            concerns = nlp_data['sentiment_counts'].get('negative', 0)
            
            f.write(f"- {happy} people liked the idea ({happy/nlp_data['total_feedback']:.0%})\n")
            f.write(f"- {neutral} people were neutral ({neutral/nlp_data['total_feedback']:.0%})\n")
            f.write(f"- {concerns} people had concerns ({concerns/nlp_data['total_feedback']:.0%})\n\n")
            
            f.write("What people like:\n")
            for i, comment in enumerate(nlp_data['samples']['positive'][:2], 1):
                f.write(f"{i}. \"{comment[:100]}...\"\n")
            
            f.write("\nMain concerns:\n")
            for i, comment in enumerate(nlp_data['samples']['negative'][:2], 1):
                f.write(f"{i}. \"{comment[:100]}...\"\n\n")
        
        # 2. What Needs Improvement
        if results.get('improvements'):
            imp_data = results['improvements']
            f.write("\n2. WHAT NEEDS IMPROVEMENT\n")
            f.write("-"*60 + "\n")
            f.write("From what people said, these are the most important things to fix:\n\n")
            
            for topic, count in imp_data['topic_counts'].items():
                f.write(f"- {topic}: {count} people talked about this\n")
            
            f.write("\nMost common words people used:\n")
            for topic in imp_data['topics']:
                f.write(f"- {', '.join(topic['top_words'][:3])}\n")
        
        # 3. Food Salt Problems
        if results.get('usage'):
            usage_data = results['usage']
            f.write("\n3. FOOD SALT PROBLEMS\n")
            f.write("-"*60 + "\n")
            f.write("People said these foods have too much salt:\n")
            f.write(f"- {usage_data['most_salty'].replace('salt_', '').replace('_', ' ').title()}\n\n")
            
            f.write("How people feel about salt in their food:\n")
            for perception, percent in usage_data['perception_stats'].items():
                f.write(f"- {perception}: {percent:.0%} people feel this way\n")
        
        # 4. Who Wants Smart Spoon
        if results.get('diet'):
            diet_data = results['diet']
            f.write("\n4. WHO WANTS SMART SPOON MOST\n")
            f.write("-"*60 + "\n")
            f.write("People with these health needs want it most:\n")
            for condition, count in diet_data['top_conditions'].items():
                f.write(f"- {condition} ({count} people)\n")
            
            f.write("\nWould people buy it?\n")
            for decision, percent in diet_data['purchase_ratio'].items():
                f.write(f"- {decision}: {percent:.0%} said this\n")
        
        # 5. Simple Recommendations
        f.write("\n5. WHAT TO DO NEXT\n")
        f.write("-"*60 + "\n")
        f.write("1. Make sure the spoon makes food taste good\n")
        f.write("2. Keep the price reasonable\n")
        f.write("3. Show how it helps people with health problems\n")
        f.write("4. Fix the salt problems in the foods people mentioned\n")
        f.write("5. Talk to the people who had concerns\n\n")
        
        f.write("="*60 + "\n")
        f.write("END OF REPORT - THANK YOU!\n")
    
    print(f"Super simple report saved as {filename}")

# ----------------------------
# MAIN EXECUTION
# ----------------------------

def main():
    # Initialize NLTK
    nltk.download('vader_lexicon', quiet=True)
    
    # Create database and table
    if not create_database_and_table():
        print("Failed to create database/table. Exiting.")
        return
    
    # Load and insert data
    df = load_and_prepare_data()
    if df is not None:
        if not insert_data_to_database(df):
            print("Failed to insert data. Continuing with analysis if data exists.")
    else:
        print("No data loaded - some analyses may not work")
    
    # Perform all analyses
    results = {
        'nlp': analyze_feedback_nlp(),
        'satisfaction': analyze_satisfaction_patterns(),
        'improvements': predict_improvements(),
        'usage': analyze_usage_data(),
        'diet': evaluate_diet_impact()
    }
    
    # Generate simple report
    generate_text_report(results)
    
    print("\n=== ANALYSIS COMPLETE ===")
    print("Generated visualizations:")
    print("- customer_sentiment.png (How people feel about Smart Spoon)")
    print("- feedback_wordcloud.png (Common words in feedback)")
    print("- satisfaction_by_age.png (Satisfaction by age and diet)")
    print("- improvement_areas.png (Key areas needing improvement - SIMPLE PIE CHART)")
    print("- food_salt_levels.png (Salt levels in different foods)")
    print("- diet_impact.png (How diet affects purchase interest)")
    print(f"\nSuper simple report saved as Simple_SmartSpoon_Report.txt")

if __name__ == "__main__":
    main()