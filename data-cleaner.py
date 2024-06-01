import streamlit as st
import pandas as pd
import uuid
from fuzzywuzzy import process
import unidecode

# Function to load and filter the remote dataset by country
@st.cache_data
def load_remote_dataset(country):
    url = 'http://35.228.140.89/eiti_database/declaration_companies.csv?_size=max'
    remote_df = pd.read_csv(url)
    filtered_df = remote_df[remote_df['country'].str.upper() == country.upper()]
    unique_companies = filtered_df.drop_duplicates(subset=['eiti_id_company'])
    unique_governments = filtered_df.drop_duplicates(subset=['eiti_id_government'])
    return unique_companies, unique_governments

# Function to generate UUID4
def generate_uuid():
    return str(uuid.uuid4())

# Function to preprocess text (convert to uppercase and remove diacritics)
def preprocess_text(text):
    return unidecode.unidecode(text).upper()

# Function to preprocess the uploaded dataset
def preprocess_dataset(df):
    df['Company'] = df['Company'].apply(preprocess_text)
    df['Government entity'] = df['Government entity'].apply(preprocess_text)
    return df

# Function to get potential matches using fuzzy matching
def get_potential_matches(unmatched_series, remote_column):
    potential_matches = unmatched_series.apply(lambda x: process.extractOne(x, remote_column)[0])
    return potential_matches

# Function to display unmatched entities with potential matches
def display_unmatched(unmatched_df, remote_df, entity_type, remote_column):
    st.subheader(f"Unmatched {entity_type.capitalize()}s")
    for index, row in unmatched_df.iterrows():
        unmatched_df.at[index, 'Potential_Match'] = st.selectbox(
            f"Potential Match for {row[entity_type]}", 
            options=['No potential match'] + remote_df[remote_column].tolist(),
            key=f"{entity_type}_match_{index}"
        )
        if unmatched_df.at[index, 'Potential_Match'] != 'No potential match':
            unmatched_df.at[index, 'EITI ID'] = remote_df[remote_df[remote_column] == unmatched_df.at[index, 'Potential_Match']][f'eiti_id_{entity_type.split()[0].lower()}'].values[0]
    st.dataframe(unmatched_df)

# Function to validate and finalize matching
def validate_matching(df, company_matches, gov_matches, unmatched_companies, unmatched_governments):
    for index, row in unmatched_companies.iterrows():
        if row['EITI ID'] == '':
            unmatched_companies.at[index, 'EITI ID'] = generate_uuid()

    for index, row in unmatched_governments.iterrows():
        if row['EITI ID'] == '':
            unmatched_governments.at[index, 'EITI ID'] = generate_uuid()

    df = pd.merge(df, company_matches[['Company', 'eiti_id_company']], on='Company', how='left')
    df = pd.merge(df, gov_matches[['Government entity', 'eiti_id_government']], on='Government entity', how='left')

    df['eiti_id_company'] = df['eiti_id_company'].combine_first(unmatched_companies.set_index('Company')['EITI ID'])
    df['eiti_id_government'] = df['eiti_id_government'].combine_first(unmatched_governments.set_index('Government entity')['EITI ID'])

    return df

# Main function to run the Streamlit app
def main():
    st.title("EITI Data Matching App")

    # SECTION 1: Upload dataset
    uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.write("Uploaded Dataset:")
        st.dataframe(df)

        # Assume the country is included in the uploaded dataset for filtering
        country = df['Country'].iloc[0]
        unique_companies, unique_governments = load_remote_dataset(country)
        
        # Preprocess the uploaded dataset and remote datasets
        df = preprocess_dataset(df)
        unique_companies['company_name'] = unique_companies['company_name'].apply(preprocess_text)
        unique_governments['government_entity'] = unique_governments['government_entity'].apply(preprocess_text)
        
        # SECTION 2: Exact matches
        st.header("Matches Found")
        company_matches = pd.merge(df, unique_companies, left_on='Company', right_on='company_name', how='inner')
        gov_matches = pd.merge(df, unique_governments, left_on='Government entity', right_on='government_entity', how='inner')
        
        st.subheader("Company Matches")
        st.dataframe(company_matches[['Company', 'eiti_id_company']])
        
        st.subheader("Government Entity Matches")
        st.dataframe(gov_matches[['Government entity', 'eiti_id_government']])
        
        # SECTION 3: Unmatched with potential matches
        st.header("Unmatched Values with Potential Matches")
        
        unmatched_companies = df[~df['Company'].isin(company_matches['Company'])]
        unmatched_governments = df[~df['Government entity'].isin(gov_matches['Government entity'])]

        unmatched_companies['Potential_Match'] = get_potential_matches(unmatched_companies['Company'], unique_companies['company_name'])
        unmatched_governments['Potential_Match'] = get_potential_matches(unmatched_governments['Government entity'], unique_governments['government_entity'])

        unmatched_companies['EITI ID'] = ''
        unmatched_governments['EITI ID'] = ''

        display_unmatched(unmatched_companies, unique_companies, 'Company', 'company_name')
        display_unmatched(unmatched_governments, unique_governments, 'Government entity', 'government_entity')
        
        # SECTION 4: Validate matching
        st.header("Validate Matching")
        if st.button("I am done matching"):
            df = validate_matching(df, company_matches, gov_matches, unmatched_companies, unmatched_governments)
            
            st.write("Matching complete. Download the updated dataset:")
            st.dataframe(df)
            
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("Download CSV", data=csv, file_name='updated_dataset.csv', mime='text/csv')

# Run the app
if __name__ == "__main__":
    main()
