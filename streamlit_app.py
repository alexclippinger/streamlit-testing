import streamlit as st
import psycopg2
import pandas as pd
import plotly.figure_factory as ff
from datetime import date


# Define query
# Uses st.experimental_memo to only rerun when the query changes or after 10 min
@st.experimental_memo(ttl=600)
def run_query(query, parameters):
    with conn.cursor() as cur:
        cur.execute(query, parameters)
        return pd.DataFrame(
            cur.fetchall(),
            columns=[desc[0] for desc in cur.description]
        )


# Initialize connection
# Uses st.experimental_singleton to only run once
@st.experimental_singleton
def init_connection():
    return psycopg2.connect(**st.secrets["postgres"])


# Download data as CSV
@st.cache
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv().encode('utf-8')


@st.cache
def get_altos_data(start_date, end_date):
    return run_query(
        """
        SELECT 
            l.*, a.zip, g.latitude, g.longitude
        FROM listings l
            INNER JOIN filtered f ON f.rental_id = l.rental_id
            JOIN addresses a ON l.address_id = a.id
            JOIN geocodes g ON a.id = g.address_id
        WHERE l.date >= %(start)s AND l.date <= %(end)s
        LIMIT 1000;
        """,
        {'start': start_date, 'end': end_date})


@st.cache
def get_all_zipcodes():
    return run_query(
        """
        SELECT distinct zipcode FROM public.zipcodes
        """, {})


def sort_unique_values(col):
    return col.drop_duplicates().sort_values()


if __name__ == "__main__":

    # Global Options
    st.set_page_config(layout="wide")

    try:
        conn = init_connection()
    except psycopg2.OperationalError:
        print("Test Error Output")

    # Header
    st.image('rdn.jpg', width=268)
    st.title('Altos Rental Data Dashboard')

    # Date inputs
    col1, col2, col3 = st.columns(3)

    with col1:
        start = st.date_input(label="Input Start Date",
                              value=date(2021, 1, 1),
                              min_value=date(2018, 1, 1),
                              max_value=date.today())

    with col2:
        end = st.date_input(label="Input End Date",
                            min_value=start,
                            max_value=date.today())

    # Run query
    if st.button("Run Query", key="query_key"):
        st.session_state['start'] = start
        st.session_state['end'] = end

    altos_data = None
    if 'start' in st.session_state:
        altos_data = get_altos_data(st.session_state['start'], st.session_state['end'])

    if altos_data is not None:
        # Print preview
        st.subheader('Data Preview:')
        st.dataframe(altos_data)

        # Select zip codes and download CSV
        zip_cont = st.container()
        select_all = st.checkbox("Select all")
        if select_all:
            zipcodes = zip_cont.multiselect('Select zip codes', sort_unique_values(altos_data['zip']),
                                            sort_unique_values(altos_data['zip']))
        else:
            zipcodes = zip_cont.multiselect('Select zip codes', sort_unique_values(altos_data['zip']))

        filtered_data = altos_data[altos_data['zip'].isin(zipcodes)]

        st.download_button(
            label="Download data as CSV",
            data=convert_df(filtered_data),
            file_name=f'altos_data_{date.today()}.csv',
            mime='text/csv',
        )

        # Create fun plots
        hist_data = [altos_data["beds"].dropna(), altos_data["baths"].dropna()]
        group_labels = ['Bedrooms', 'Bathrooms']
        fig = ff.create_distplot(
            hist_data, group_labels, bin_size=[.1, .25, .5])

        st.subheader("Data Summary")
        st.plotly_chart(fig, use_container_width=True)

        st.map(data=filtered_data.dropna(subset=["latitude", "longitude"]))
