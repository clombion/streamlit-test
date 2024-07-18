import streamlit as st
import pandas as pd
import altair as alt
from urllib.request import Request, urlopen

# -----------------------------
# Data Loading Module
# -----------------------------

@st.cache_data
def load_data(url):
    req = Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:77.0) Gecko/20100101 Firefox/77.0')
    content = urlopen(req)
    return pd.read_csv(content, on_bad_lines='skip').drop(columns=['rowid'], errors='ignore')

def set_index(dataframe, column):
    dataframe.set_index(column, inplace=True)

# URLs to datasets
about_url = 'https://soe-database.eiti.org/eiti_database/about.csv?_size=max'
agencies_url = 'https://soe-database.eiti.org/eiti_database/agencies.csv?_size=max'
companies_url = 'https://soe-database.eiti.org/eiti_database/companies.csv?_size=max'
projects_url = 'https://soe-database.eiti.org/eiti_database/projects.csv?_size=max'
countries_svg_url = 'https://raw.githubusercontent.com/clombion/streamlit-test/main/countries_svg.csv'

# Load datasets
about = load_data(about_url)
agencies = load_data(agencies_url)
companies = load_data(companies_url)
projects = load_data(projects_url)
countries_svg = load_data(countries_svg_url)

# Set the year as the index for all datasets
set_index(about, 'start_date')
set_index(agencies, 'start_date')
set_index(companies, 'start_date')
set_index(projects, 'start_date')

# -----------------------------
# Styling Module
# -----------------------------

def apply_custom_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&family=Oswald:wght@400;700&display=swap');
        
        .report-title {
            font-family: 'Oswald', sans-serif;
            font-weight: bold;
            color: #003366;
            text-align: left;
            margin-top: 20px;
            margin-bottom: 20px;
        }
        .section-title {
            font-family: 'Roboto', sans-serif;
            font-size: 1.5em;
            color: grey;
            margin-top: 20px;
            margin-bottom: 10px;
        }
        .variable-text {
            font-size: 1.5em;
            text-align: left;
            margin: 20px 0;
        }
        .highlight {
            color: #0068C9;
        }
        .sidebar-title {
            font-family: 'Roboto', sans-serif;
            font-size: 1.5em;
            color: black;
            text-align: left;
        }
        .sidebar-text {
            font-family: 'Roboto', sans-serif;
            font-size: 1em;
            margin-top: 20px;
        }
        .dataframe {
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 15px;
            margin-bottom: 20px;
            background-color: #f9f9f9;
        }
        .country-svg {
            margin-top: 20px;
            margin-bottom: 20px;
            text-align: center;
        }
        .expander-container .stExpander {
            border: none;
        }
        .expander-container .stExpanderContent {
            padding: 0;
        }
        .pie-chart {
            margin-top: 40px;
        }
        .legend-space {
            margin-bottom: 30px;
        }
        .section-space {
            margin-top: 40px;
        }
        </style>
    """, unsafe_allow_html=True)

# Apply custom CSS for styling
apply_custom_css()

# -----------------------------
# UI Functions Module
# -----------------------------

def sidebar():
    # Sidebar title with logo
    st.sidebar.markdown('<div class="sidebar-title" style="font-size: 1.5em;">EITI DATA EXPLORER</div>', unsafe_allow_html=True)
    
    # Sidebar for country selection
    country_list = about['country_or_area_name'].unique()
    selected_country = st.sidebar.selectbox('Select a Country', country_list)
    
    # Display SVG for selected country
    display_country_svg(selected_country)
    
    # Add text below the SVG in the sidebar
    st.sidebar.markdown("""
    <div class='sidebar-text'>
        Unofficial prototype dashboard developed by 
        <a href='https://civicliteracies.org' target='_blank'>Civic Literacy Initiative</a> 
        with <a href='https://eiti.org' target='_blank'>EITI</a> data.
    </div>
    """, unsafe_allow_html=True)
    
    return selected_country

def display_main_title():
    st.markdown('<h1 class="report-title">EITI Country Revenue Report</h1>', unsafe_allow_html=True)

def display_country_svg(selected_country):
    country_svg_row = countries_svg[countries_svg['Country'] == selected_country]
    if not country_svg_row.empty:
        svg_code = country_svg_row['SVG Path'].values[0]
        st.sidebar.markdown(f"""
        <div class="country-svg">
            {svg_code}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.sidebar.markdown(f"""
        <div class="country-svg">
            <p>No SVG available for {selected_country}</p>
        </div>
        """, unsafe_allow_html=True)

def display_country_report(selected_country):
    # Filter data for selected country
    country_data = about[about['country_or_area_name'] == selected_country]
    country_agencies = agencies[agencies['country'] == selected_country]
    country_companies = companies[companies['country'] == selected_country]
    country_projects = projects[projects['country'] == selected_country]

    # Count unique companies and projects
    unique_companies = country_companies.drop_duplicates(subset='eiti_id_company').shape[0]
    unique_projects = country_companies.drop_duplicates(subset=['eiti_id_project', 'company_type']).shape[0]

    # Get earliest and latest years
    earliest_year = country_data.index.min()[:4]
    latest_year = country_data.index.max()[:4]

    # Calculate total revenue and top 3 revenue streams
    total_revenue = country_agencies['revenue_value'].sum()
    if total_revenue >= 1e9:
        total_revenue_str = f"{total_revenue / 1e9:.2f} billion"
    else:
        total_revenue_str = f"{total_revenue / 1e6:.2f} million"

    top_3_revenue_streams = country_agencies.groupby('revenue_stream_name')['revenue_value'].sum().sort_values(ascending=False).head(3).index.tolist()
    top_3_revenue_streams_str = ", ".join(top_3_revenue_streams)

    # Display the sentence after the main title
    if earliest_year == latest_year:
        st.markdown(f"""
        <p class='variable-text'>
        <strong class="highlight">{selected_country}</strong> has reported <strong class="highlight">{unique_companies}</strong> companies operating on its territory, across <strong class="highlight">{unique_projects}</strong> projects. <strong class="highlight">{selected_country}</strong>’s extractive industry generated a total of <strong class="highlight">{total_revenue_str}</strong> dollars in <strong class="highlight">{latest_year}</strong>. Its top 3 revenue streams are: <strong class="highlight">{top_3_revenue_streams_str}</strong>.
        </p>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <p class='variable-text'>
        <strong class="highlight">{selected_country}</strong> has reported <strong class="highlight">{unique_companies}</strong> companies operating on its territory, across <strong class="highlight">{unique_projects}</strong> projects. <strong class="highlight">{selected_country}</strong>’s extractive industry generated a total of <strong class="highlight">{total_revenue_str}</strong> dollars between <strong class="highlight">{earliest_year}</strong> and <strong class="highlight">{latest_year}</strong>. Its top 3 revenue streams are: <strong class="highlight">{top_3_revenue_streams_str}</strong>.
        </p>
        """, unsafe_allow_html=True)

    # Visualization for revenue streams using Altair
    st.markdown(f'<h2 class="section-title">Revenue between {earliest_year} and {latest_year}</h2>', unsafe_allow_html=True)
    revenue_streams = country_agencies.groupby('revenue_stream_name')['revenue_value'].sum().sort_values(ascending=False) / 1e6

    revenue_df = revenue_streams.reset_index()
    revenue_df.columns = ['Revenue Stream', 'Revenue (Million USD)']

    chart = alt.Chart(revenue_df).mark_bar().encode(
        x=alt.X('Revenue Stream', sort='-y'),
        y=alt.Y('Revenue (Million USD)', title='Revenue (Million USD)'),
        tooltip=['Revenue Stream', 'Revenue (Million USD)']
    ).properties(
        width=alt.Step(80)
    )

    st.altair_chart(chart, use_container_width=True)
    st.markdown('<div class="section-space"></div>', unsafe_allow_html=True)

    # Calculate revenue breakdown by company type
    company_type_revenue = country_companies.groupby('company_type')['revenue_value'].sum().reset_index()
    company_type_revenue['Percentage'] = (company_type_revenue['revenue_value'] / company_type_revenue['revenue_value'].sum()) * 100

    # Filter unique projects by company type
    unique_projects_by_company_type = country_companies.drop_duplicates(subset=['eiti_id_project', 'company_type'])

    # Colors from EITI logo
    eiti_colors = ["#0076A8", "#00A3E0"]

    # Pie chart for revenue breakdown by company type
    col1, col2 = st.columns([0.4, 0.6])
    with col1:
        pie_chart = alt.Chart(company_type_revenue).mark_arc().encode(
            theta=alt.Theta(field="revenue_value", type="quantitative"),
            color=alt.Color(field="company_type", type="nominal", scale=alt.Scale(range=eiti_colors)),
            tooltip=['company_type', 'revenue_value', 'Percentage']
        ).properties(
            width=200,
            height=200
        ).configure_legend(
            orient='bottom',
            title=None,
            labelFontSize=12,
            titleFontSize=12,
            labelPadding=20  # Add distance between the chart and the legend
        ).configure_view(
            strokeOpacity=0
        )

        st.altair_chart(pie_chart, use_container_width=True)
        st.markdown('<div class="legend-space"></div>', unsafe_allow_html=True)

    # Generate sentence based on the distribution of revenue
    if not company_type_revenue.empty:
        if len(company_type_revenue) > 1:
            company_type1 = company_type_revenue.iloc[0]['company_type']
            company_type1_revenue = company_type_revenue.iloc[0]['Percentage']
            company_type2 = company_type_revenue.iloc[1]['company_type']
            company_type2_revenue = company_type_revenue.iloc[1]['Percentage']

            company_type1_projects = unique_projects_by_company_type[unique_projects_by_company_type['company_type'] == company_type1].shape[0]
            company_type2_projects = unique_projects_by_company_type[unique_projects_by_company_type['company_type'] == company_type2].shape[0]

            if company_type1 == "Private":
                company_type1_text = f"{company_type1} companies"
            else:
                company_type1_text = company_type1

            if company_type2 == "Private":
                company_type2_text = f"{company_type2} companies"
            else:
                company_type2_text = company_type2

            if abs(company_type1_revenue - company_type2_revenue) <= 10:
                sentence = (f"A similar amount of revenue generated by the extractive industries of "
                            f"<strong class='highlight'>{selected_country}</strong> is from "
                            f"<strong class='highlight'>{company_type1_text}</strong> ({company_type1_revenue:.2f}%), "
                            f"with <strong class='highlight'>{company_type2_text}</strong> representing "
                            f"{company_type2_revenue:.2f}% of payments. <strong class='highlight'>{company_type1_text}</strong> "
                            f"generated this amount across <strong class='highlight'>{company_type1_projects}</strong> projects, "
                            f"in comparison to <strong class='highlight'>{company_type2_projects}</strong> projects managed by "
                            f"<strong class='highlight'>{company_type2_text}</strong>.")
            elif abs(company_type1_revenue - company_type2_revenue) <= 40:
                majority_type = company_type1_text if company_type1_revenue > company_type2_revenue else company_type2_text
                minority_type = company_type2_text if company_type1_revenue > company_type2_revenue else company_type1_text
                majority_revenue = company_type1_revenue if company_type1_revenue > company_type2_revenue else company_type2_revenue
                minority_revenue = company_type2_revenue if company_type1_revenue > company_type2_revenue else company_type1_revenue
                majority_projects = company_type1_projects if company_type1_revenue > company_type2_revenue else company_type2_projects
                minority_projects = company_type2_projects if company_type1_revenue > company_type2_revenue else company_type1_projects
                sentence = (f"The majority of revenue generated by the extractive industries of "
                            f"<strong class='highlight'>{selected_country}</strong> is from "
                            f"<strong class='highlight'>{majority_type}</strong> ({majority_revenue:.2f}%), "
                            f"with <strong class='highlight'>{minority_type}</strong> representing "
                            f"{minority_revenue:.2f}% of payments. <strong class='highlight'>{majority_type}</strong> "
                            f"generated this amount across <strong class='highlight'>{majority_projects}</strong> projects, "
                            f"in comparison to <strong class='highlight'>{minority_projects}</strong> projects managed by "
                            f"<strong class='highlight'>{minority_type}</strong>.")
            else:
                overwhelming_type = company_type1_text if company_type1_revenue > company_type2_revenue else company_type2_text
                minor_type = company_type2_text if company_type1_revenue > company_type2_revenue else company_type1_text
                overwhelming_revenue = company_type1_revenue if company_type1_revenue > company_type2_revenue else company_type2_revenue
                minor_revenue = company_type2_revenue if company_type1_revenue > company_type2_revenue else company_type1_revenue
                overwhelming_projects = company_type1_projects if company_type1_revenue > company_type2_revenue else company_type2_projects
                minor_projects = company_type2_projects if company_type1_revenue > company_type2_revenue else company_type1_projects
                sentence = (f"An overwhelming majority of revenue generated by the extractive industries of "
                            f"<strong class='highlight'>{selected_country}</strong> is from "
                            f"<strong class='highlight'>{overwhelming_type}</strong> ({overwhelming_revenue:.2f}%), "
                            f"with <strong class='highlight'>{minor_type}</strong> representing "
                            f"{minor_revenue:.2f}% of payments. <strong class='highlight'>{overwhelming_type}</strong> "
                            f"generated this amount across <strong class='highlight'>{overwhelming_projects}</strong> projects, "
                            f"in comparison to <strong class='highlight'>{minor_projects}</strong> projects managed by "
                            f"<strong class='highlight'>{minor_type}</strong>.")
        else:
            company_type1 = company_type_revenue.iloc[0]['company_type']
            company_type1_revenue = company_type_revenue.iloc[0]['Percentage']
            company_type1_projects = unique_projects_by_company_type[unique_projects_by_company_type['company_type'] == company_type1].shape[0]
            if company_type1 == "Private":
                company_type1_text = f"{company_type1} companies"
            else:
                company_type1_text = company_type1
            sentence = (f"All the revenue generated by the extractive industries of "
                        f"<strong class='highlight'>{selected_country}</strong> is from "
                        f"<strong class='highlight'>{company_type1_text}</strong> ({company_type1_revenue:.2f}%).")

        with col2:
            st.markdown(sentence, unsafe_allow_html=True)

    # Display other data sections
    with st.expander("Government Agencies"):
        st.write(country_agencies)

    with st.expander("Companies"):
        st.write(country_companies)

    with st.expander("Projects"):
        st.write(country_projects)

    # Display general information inside expander called "Metadata"
    with st.expander("Metadata"):
        st.write(country_data)

    # Create CSV summary data
    summary_data = []
    for year in range(int(earliest_year), int(latest_year) + 1):
        year_data = country_agencies[country_agencies.index.str.startswith(str(year))]
        year_revenue = year_data['revenue_value'].sum()
        top_3_year_revenue_streams = year_data.groupby('revenue_stream_name')['revenue_value'].sum().sort_values(ascending=False).head(3).index.tolist()
        top_3_year_revenue_streams_str = ", ".join(top_3_year_revenue_streams)
        summary_data.append({
            'Country': selected_country,
            'Year': year,
            'Reporting Companies': unique_companies,
            'Projects': unique_projects,
            'Revenue': year_revenue,
            'Top 3 Revenue Streams': top_3_year_revenue_streams_str
        })

    summary_df = pd.DataFrame(summary_data)

    # Downloadable link for CSV
    st.markdown('<h2 class="section-title">Download Summary Data</h2>', unsafe_allow_html=True)
    csv = summary_df.to_csv(index=False)
    st.download_button('Download CSV', csv, file_name=f'{selected_country}_summary_report.csv')

# -----------------------------
# Main Function
# -----------------------------

def main():
    selected_country = sidebar()
    display_main_title()
    display_country_report(selected_country)

if __name__ == "__main__":
    main()
