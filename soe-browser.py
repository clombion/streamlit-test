import streamlit as st
import pandas as pd
import altair as alt
import numpy as np
import re

# -----------------------------
# Helper Functions Module
# -----------------------------

@st.cache_data
def get_data():
    """
    Load and cache data from the Datasette API.
    
    Returns:
        pd.DataFrame: DataFrame containing the loaded data.
    """
    return pd.read_csv("http://35.228.140.89/eiti_database.csv?sql=SELECT%0D%0A++++scra.*%2C%0D%0A++++REPLACE%28REPLACE%28ca.commodities%2C+%27n%2Fa%27%2C+%27%27%29%2C+%27n%2Fv%27%2C+%27%27%29+AS+commodities%0D%0AFROM%0D%0A++++soe_companies_revenue_annual+AS+scra%0D%0ALEFT+JOIN+%28%0D%0A++++SELECT%0D%0A++++++++dc.eiti_id_company+AS+eiti_id_declaration%2C%0D%0A++++++++dc.year%2C%0D%0A++++++++GROUP_CONCAT%28DISTINCT+dp.commodities%29+AS+commodities%0D%0A++++FROM%0D%0A++++++++declaration_companies+AS+dc%0D%0A++++JOIN%0D%0A++++++++declaration_projects+AS+dp%0D%0A++++ON%0D%0A++++++++dc.eiti_id_project+%3D+dp.eiti_id_project%0D%0A++++GROUP+BY%0D%0A++++++++dc.eiti_id_company%2C%0D%0A++++++++dc.year%0D%0A%29+AS+ca%0D%0AON%0D%0A++++scra.eiti_id_company+%3D+ca.eiti_id_declaration%0D%0AAND%0D%0A++++scra.year+%3D+ca.year%3B%0D%0A&_size=max")

def filter_data_by_company(data, company_name):
    """
    Filter the data for a specific company.
    
    Args:
        data (pd.DataFrame): The original data.
        company_name (str): The name of the company to filter by.
    
    Returns:
        pd.DataFrame: Filtered data for the specified company.
    """
    return data[data['company_name'] == company_name]

def process_commodities(commodities):
    processed = []
    for item in commodities:
        if pd.isna(item):
            continue  # Skip NaN values
        # Remove text within parentheses
        item = re.sub(r'\s*\(.*?\)\s*', '', str(item))
        processed.append(item.strip())
    # If the list is empty or contains only NaNs, return 'unknown commodities'
    if not processed:
        return ['unknown commodities']
    return processed

def compute_company_info(filtered_data):
    """
    Compute company information such as the number of reports,
    the earliest report year, and the latest report year.
    
    Args:
        filtered_data (pd.DataFrame): The filtered data for a company.
    
    Returns:
        dict: A dictionary containing company information.
    """
    num_reports = len(filtered_data)
    earliest_year = str(filtered_data['year'].min())
    latest_year = str(filtered_data['year'].max())
    total_revenue_usd = filtered_data['revenue_value_usd'].sum()
    share_of_national_payments = filtered_data['percentage_country_usd'].mean()
    
    # Ensure all entries in 'commodities' are lists
    filtered_data['commodities'] = filtered_data['commodities'].apply(lambda x: x if isinstance(x, list) else [x])

    # Replace arrays of NaNs with a single NaN
    filtered_data['commodities'] = filtered_data['commodities'].apply(process_commodities)

    # Combine and deduplicate arrays in 'commodities'
    unique_commodities = list(set([item for sublist in filtered_data['commodities'] for item in sublist]))
    
    company_info = {
        'Name': filtered_data['company_name'].iloc[0],
        'Country': filtered_data['country'].iloc[0],
        'Number of Reports': num_reports,
        'Earliest Report Year': earliest_year,
        'Latest Report Year': latest_year,
        'Total Revenue USD': total_revenue_usd,
        'Share of National Payments': share_of_national_payments,
        'Commodities': unique_commodities
    }
    
    return company_info

def render_other_companies(data, country, current_company):
    """
    Render a list of other companies from the same country.
    
    Args:
        data (pd.DataFrame): The original data.
        country (str): The country name.
        current_company (str): The current company name.
    """
    other_companies = data[(data['country'] == country) & (data['company_name'] != current_company)]
    if not other_companies.empty:
        st.markdown(f"<h3 class='other-soes-heading'>Other SOEs from {country}</h3>", unsafe_allow_html=True)
        cols = st.columns(2)
        companies = other_companies['company_name'].unique()
        for i, company in enumerate(companies):
            col = cols[i % 2]
            if col.button(company):
                st.session_state.temp_selected_company = company
                st.experimental_rerun()

# -----------------------------
# UI Functions Module
# -----------------------------

def render_company_info(company_info):
    """
    Render the company information as styled content in the Streamlit app.
    
    Args:
        company_info (dict): A dictionary containing company information.
    """
    # Custom CSS for styling
    custom_css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700&family=Open+Sans:wght@400;700&family=Oswald:wght@400;700&display=swap');
    
    body {
        font-family: 'Open Sans', sans-serif;
    }
    .title {
        font-family: 'Oswald', sans-serif;
        font-weight: 100 ;
    }
    .subtitle {
        font-family: 'Oswald', sans-serif;
        font-size: 1.2em;
        color: dark grey;
        margin-bottom: 20px;
    }
    .company-info {
        font-family: 'Open Sans', sans-serif;
        line-height: 1.6;
        font-size: 18px;
        margin: 10px 0;
    }
    .company-info strong {
        font-family: 'Montserrat', sans-serif;
        font-weight: bold;
        color: #1a73e8;
        text-decoration: underline dotted;
    }
    .custom-link {
        color: #1a73e8;
        text-decoration: none;
        font-family: 'Open Sans', sans-serif;
        font-size: 16px;
    }
    .custom-link:hover {
        text-decoration: underline;
    }
    .normal-text {
        font-family: 'Open Sans', sans-serif;
        font-size: 16px;
        font-weight: normal;
        margin-bottom: 10px;
    }
    .button-as-link {
        background: none;
        border: none;
        color: #1a73e8;
        text-decoration: none;
        font-family: 'Open Sans', sans-serif;
        font-size: 14px;
        cursor: pointer;
        text-align: left;
        margin-bottom: 20px;
    }
    .button-as-link:hover {
        text-decoration: underline;
    }
    .button-as-link::before {
        content: '➜  ';
    }
    .other-soes-heading {
        margin-bottom: 20px;
    }
    .stButton>button {
        width: 80% !important;
        text-align: left !important;
        display: block;
        margin: auto;
        float:left;
    }
    </style>
    """
    commodities_str = ', '.join(company_info['Commodities'])

    # Company information sentence with styled variables
    company_sentence = (
        f"<div class='company-info'><strong>{company_info['Name']}</strong> is a state-owned enterprise from <strong>{company_info['Country']}</strong> dealing in <strong>{commodities_str}</strong>."
        f"The company paid a declared amount of <strong>{company_info['Total Revenue USD'] / 1e6:,.2f}</strong> million USD in taxes for its extractives activities "
        f"between <strong>{company_info['Earliest Report Year']}</strong> and <strong>{company_info['Latest Report Year']}</strong>, representing <strong>{company_info['Share of National Payments']}</strong>% of the sector's contribution to the national budget over that period..</div>"
    )

    # Display the custom CSS and company information
    st.markdown(custom_css + company_sentence, unsafe_allow_html=True)


def render_revenue_chart(filtered_data):
    """
    Render the revenue chart in the Streamlit app.
    
    Args:
        filtered_data (pd.DataFrame): The filtered data for a company.
    """
    st.write("### Revenue Over Time")
    st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)  # Add space between title and chart

    filtered_data['revenue_value_usd_million'] = filtered_data['revenue_value_usd'] / 1e6

    chart = alt.Chart(filtered_data).mark_line(point=True).encode(
        x=alt.X('year:O', title='Year'),
        y=alt.Y('revenue_value_usd_million:Q', title='Revenue (Million USD)'),
        tooltip=[alt.Tooltip('revenue_value_usd_million:Q', title='Revenue (Million USD)')]
    ).properties(
        width=700,
        height=400
    ).configure_axis(
        labelFontSize=12,
        titleFontSize=14
    ).configure_title(
        fontSize=16
    ).configure_point(
        size=50
    )

    st.altair_chart(chart, use_container_width=True)

def render_detailed_data_table(filtered_data):
    """
    Render the detailed data table in the Streamlit app.
    
    Args:
        filtered_data (pd.DataFrame): The filtered data for a company.
    """
    st.write("### Detailed Data")
    filtered_data = filtered_data.drop(columns=['eiti_id_company', 'company_name', 'country'])
    filtered_data = filtered_data.set_index('year')
    num_rows = len(filtered_data)
    table_height = 100 + num_rows * 25  # Adjust the multiplier and base height as needed
    st.dataframe(filtered_data, height=table_height)

# -----------------------------
# Main Application Logic
# -----------------------------

def update_selected_country():
    st.session_state.selected_country = st.session_state.country_select

def update_selected_company():
    st.session_state.selected_company = st.session_state.company_select

def main():
    # Load data
    data = get_data()

    # Initialize session state for selected country and company if not already set
    if 'selected_country' not in st.session_state:
        st.session_state.selected_country = 'Global'
    if 'selected_company' not in st.session_state:
        st.session_state.selected_company = data['company_name'].unique()[0]

    # Handle button clicks to update selected company
    if 'temp_selected_company' in st.session_state:
        st.session_state.selected_company = st.session_state.temp_selected_company
        del st.session_state['temp_selected_company']
        st.experimental_rerun()
    
    st.sidebar.image("https://totalenergies.com/sites/g/files/nytnzq121/files/styles/w_1110/public/images/2022-04/Logo_EITI.png")

    st.sidebar.markdown(
        """
        <h2 style="margin-bottom: 20px; font-size:2em; font-weight: 50 ;">SOE DATA EXPLORER</h2>
        """, 
        unsafe_allow_html=True
    )

    # Get list of countries with an added 'Global' option
    countries = ['Global'] + sorted(data['country'].unique().tolist())
    selected_country = st.sidebar.selectbox(
        'Select a country:',
        countries,
        index=countries.index(st.session_state.selected_country),
        key='country_select',
        on_change=update_selected_country
    )

    # Filter company names based on selected country
    if selected_country == 'Global':
        company_names = data['company_name'].unique()
    else:
        company_names = data[data['country'] == selected_country]['company_name'].unique()

    # Ensure selected company is valid
    if st.session_state.selected_company not in company_names:
        st.session_state.selected_company = company_names[0]

    selected_company = st.sidebar.selectbox(
        'Select a company:',
        company_names,
        index=list(company_names).index(st.session_state.selected_company),
        key='company_select',
        on_change=update_selected_company
    )

    st.sidebar.markdown(
        """
        <div class="normal-text" style="margin-top: 20px">
        Interactive data explorer based on <a href="https://eiti.org" target="_blank">EITI data</a>. 
        By <a href="https://civicliteraci.es" target="_blank">Civic Literacy Initiative</a>.
        </div>
        """, 
        unsafe_allow_html=True
    )

    # Filter data based on selected company
    filtered_data = filter_data_by_company(data, selected_company)

    # Compute company information
    company_info = compute_company_info(filtered_data)

    # Main page title with improved presentation
    st.markdown(
        f"""
        <div style="text-align: left; margin-bottom: 5px;">
            <h1 class="title" style="margin: 0; font-size: 3em;">{company_info['Name']}</h1>
        </div>
        """, 
        unsafe_allow_html=True
    )

    # Render the company info
    render_company_info(company_info)

    # Render UI components
    render_revenue_chart(filtered_data)
    render_detailed_data_table(filtered_data)
    
    # Render other companies from the same country
    render_other_companies(data, company_info['Country'], company_info['Name'])

if __name__ == "__main__":
    main()
