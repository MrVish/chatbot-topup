"""
RAG Tool for glossary and schema retrieval using Chroma vector database.

This module provides semantic search capabilities over KPI definitions,
schema descriptions, and Q&A exemplars to support the Memory Agent.
"""

import os
from typing import List

import chromadb
from chromadb.config import Settings
from langchain_openai import OpenAIEmbeddings


class RAGTool:
    """
    Retrieval-Augmented Generation tool for glossary and schema queries.
    
    Uses Chroma vector database with OpenAI embeddings to provide semantic
    search over KPI definitions, schema descriptions, and Q&A exemplars.
    """
    
    def __init__(self, persist_directory: str = "./data/chroma"):
        """
        Initialize the RAG tool with Chroma client and collection.
        
        Args:
            persist_directory: Path to persistent Chroma storage
        """
        self.persist_directory = persist_directory
        
        # Ensure directory exists
        os.makedirs(persist_directory, exist_ok=True)
        
        # Initialize Chroma client with persistent storage
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Initialize OpenAI embeddings
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small"
        )
        
        # Get or create collection
        self.collection_name = "topup_glossary"
        self._initialize_collection()
    
    def _initialize_collection(self):
        """Initialize or get existing collection with sample documents."""
        try:
            # Try to get existing collection
            self.collection = self.client.get_collection(
                name=self.collection_name
            )
            
            # Check if collection is empty
            if self.collection.count() == 0:
                self._index_documents()
        except Exception:
            # Create new collection if it doesn't exist
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "Topup KPI definitions and schema glossary"}
            )
            self._index_documents()
    
    def _index_documents(self):
        """Index KPI definitions, schema descriptions, and Q&A exemplars."""
        documents = self._get_sample_documents()
        
        # Generate embeddings for all documents
        texts = [doc["text"] for doc in documents]
        embeddings = self.embeddings.embed_documents(texts)
        
        # Add documents to collection
        self.collection.add(
            documents=texts,
            embeddings=embeddings,
            metadatas=[doc["metadata"] for doc in documents],
            ids=[doc["id"] for doc in documents]
        )
    
    def _get_sample_documents(self) -> List[dict]:
        """
        Get sample documents for indexing.
        
        Returns:
            List of documents with text, metadata, and IDs
        """
        documents = []
        
        # KPI Definitions
        kpi_definitions = [
            {
                "id": "kpi_app_submits_amt",
                "text": "App Submits (Amount): The total dollar amount of loan applications submitted by customers. Calculated as SUM(app_submit_amt). This is the default metric when users ask about 'app submits' or 'submissions' without specifying count.",
                "metadata": {"type": "kpi", "category": "amount"}
            },
            {
                "id": "kpi_app_submits_count",
                "text": "App Submits (Count): The number of loan applications submitted by customers. Calculated as COUNT(app_submit_d). Only used when users explicitly request 'number of app submits' or 'count of submissions'.",
                "metadata": {"type": "kpi", "category": "count"}
            },
            {
                "id": "kpi_app_approvals_amt",
                "text": "App Approvals (Amount): The total dollar amount of loan applications that were approved. Calculated as SUM(CASE WHEN cr_appr_flag = 1 THEN approval_amt ELSE 0 END). This is the default metric when users ask about 'app approvals' or 'approvals' without specifying count.",
                "metadata": {"type": "kpi", "category": "amount"}
            },
            {
                "id": "kpi_app_approvals_count",
                "text": "App Approvals (Count): The number of loan applications that were approved. Calculated as SUM(cr_appr_flag). Only used when users explicitly request 'number of app approvals' or 'count of approvals'.",
                "metadata": {"type": "kpi", "category": "count"}
            },
            {
                "id": "kpi_issuances_amt",
                "text": "Issuances (Amount): The total dollar amount of loans that were issued to customers. Calculated as SUM(CASE WHEN issued_flag = 1 THEN issued_amt ELSE 0 END). This is the default metric when users ask about 'issuances' without specifying count.",
                "metadata": {"type": "kpi", "category": "amount"}
            },
            {
                "id": "kpi_issuances_count",
                "text": "Issuances (Count): The number of loans that were issued to customers. Calculated as SUM(issued_flag). Only used when users explicitly request 'number of issuances' or 'count of issuances'.",
                "metadata": {"type": "kpi", "category": "count"}
            },
            {
                "id": "kpi_approval_rate",
                "text": "Approval Rate: The percentage of offered applications that were approved. Calculated as SUM(cr_appr_flag) / NULLIF(SUM(offered_flag), 0). This metric shows how many applications that received an offer were ultimately approved.",
                "metadata": {"type": "kpi", "category": "rate"}
            },
            {
                "id": "kpi_funding_rate",
                "text": "Funding Rate: The percentage of submitted applications that resulted in issued loans. Calculated as SUM(issued_flag) / NULLIF(COUNT(app_submit_d), 0). This metric shows the overall conversion from submission to issuance.",
                "metadata": {"type": "kpi", "category": "rate"}
            },
            {
                "id": "kpi_average_apr",
                "text": "Average APR: The average Annual Percentage Rate offered to customers. Calculated as AVG(offer_apr). This metric indicates the average interest rate across all offers.",
                "metadata": {"type": "kpi", "category": "average"}
            },
            {
                "id": "kpi_average_fico",
                "text": "Average FICO: The average FICO credit score of applicants. Calculated as AVG(cr_fico). This metric indicates the average creditworthiness of the customer base.",
                "metadata": {"type": "kpi", "category": "average"}
            },
            {
                "id": "kpi_forecast_delta",
                "text": "Forecast Delta: The difference between actual and forecasted issuance amounts. Calculated as actual_issuance - forecast_issuance. Positive values indicate over-performance, negative values indicate under-performance.",
                "metadata": {"type": "kpi", "category": "forecast"}
            },
            {
                "id": "kpi_forecast_accuracy",
                "text": "Forecast Accuracy: The ratio of actual to forecasted issuance. Calculated as actual_issuance / NULLIF(forecast_issuance, 0). Values above 1.0 indicate over-performance, values below 1.0 indicate under-performance.",
                "metadata": {"type": "kpi", "category": "forecast"}
            }
        ]
        
        documents.extend(kpi_definitions)
        
        # Schema Descriptions
        schema_descriptions = [
            {
                "id": "schema_cps_tb",
                "text": "cps_tb Table: Customer acquisition table containing submission, approval, and issuance data. Key columns include app_submit_d (submission date), apps_approved_d (approval date), issued_d (issuance date), and various amount columns. Also includes segment dimensions like channel, grade, prod_type, repeat_type, term, cr_fico_band, and purpose.",
                "metadata": {"type": "schema", "table": "cps_tb"}
            },
            {
                "id": "schema_forecast_df",
                "text": "forecast_df Table: Forecast table containing predicted vs actual issuance metrics. Key columns include date, channel, grade, forecast_issuance, and actual_issuance. Used for forecast accuracy analysis.",
                "metadata": {"type": "schema", "table": "forecast_df"}
            },
            {
                "id": "field_channel",
                "text": "Channel: Marketing channel through which the customer was acquired. Values include OMB (Online Marketing Brand), Email, Search, D2LC (Direct to Lending Club), DM (Direct Mail), LT (Lending Tree), Experian, Karma, and Small Partners.",
                "metadata": {"type": "field", "field": "channel"}
            },
            {
                "id": "field_grade",
                "text": "Grade: Credit grade assigned to the loan. Values include P1 (highest quality), P2, P3, P4, P5, and P6 (lowest quality). Lower grades typically have higher interest rates.",
                "metadata": {"type": "field", "field": "grade"}
            },
            {
                "id": "field_prod_type",
                "text": "Product Type: Type of loan product. Values include Prime (prime credit customers), NP (near-prime), and D2P (direct to prime).",
                "metadata": {"type": "field", "field": "prod_type"}
            },
            {
                "id": "field_repeat_type",
                "text": "Repeat Type: Customer type indicating whether this is a new or returning customer. Values include Repeat (returning customer) and New (first-time customer).",
                "metadata": {"type": "field", "field": "repeat_type"}
            },
            {
                "id": "field_term",
                "text": "Term: Loan term in months. Common values include 36, 48, 60, 72, and 84 months. Longer terms typically have lower monthly payments but higher total interest.",
                "metadata": {"type": "field", "field": "term"}
            },
            {
                "id": "field_cr_fico_band",
                "text": "FICO Band: Credit score range of the applicant. Values include <640 (subprime), 640-699 (near-prime), 700-759 (prime), and 760+ (super-prime). Higher FICO scores indicate better creditworthiness.",
                "metadata": {"type": "field", "field": "cr_fico_band"}
            },
            {
                "id": "field_purpose",
                "text": "Purpose: The stated purpose of the loan. Values include debt_consolidation (most common), home_improvement, major_purchase, medical, car, and other.",
                "metadata": {"type": "field", "field": "purpose"}
            }
        ]
        
        documents.extend(schema_descriptions)
        
        # Q&A Exemplars
        qa_exemplars = [
            {
                "id": "qa_what_is_funding_rate",
                "text": "Q: What is funding rate? A: Funding rate is the percentage of submitted applications that resulted in issued loans. It's calculated as the number of issued loans divided by the number of submitted applications. This metric shows the overall conversion from submission to issuance.",
                "metadata": {"type": "qa", "question": "what is funding rate"}
            },
            {
                "id": "qa_what_is_approval_rate",
                "text": "Q: What is approval rate? A: Approval rate is the percentage of offered applications that were approved. It's calculated as the number of approved applications divided by the number of offered applications. This metric shows how many applications that received an offer were ultimately approved.",
                "metadata": {"type": "qa", "question": "what is approval rate"}
            },
            {
                "id": "qa_difference_submits_approvals",
                "text": "Q: What's the difference between app submits and app approvals? A: App submits are loan applications that customers have submitted, while app approvals are applications that have been approved by the credit team. By default, these metrics refer to dollar amounts (total loan amounts), not counts. The approval rate shows what percentage of offered applications were approved.",
                "metadata": {"type": "qa", "question": "difference between submits and approvals"}
            },
            {
                "id": "qa_what_is_issuance",
                "text": "Q: What is issuance? A: Issuance refers to loans that have been fully funded and issued to customers. By default, this metric refers to the total dollar amount of issued loans, not the count. It represents the final step in the customer acquisition funnel after submission and approval.",
                "metadata": {"type": "qa", "question": "what is issuance"}
            },
            {
                "id": "qa_what_are_channels",
                "text": "Q: What are the different channels? A: Channels are the marketing sources through which customers are acquired. They include OMB (Online Marketing Brand), Email, Search, D2LC (Direct to Lending Club), DM (Direct Mail), LT (Lending Tree), Experian, Karma, and Small Partners.",
                "metadata": {"type": "qa", "question": "what are channels"}
            },
            {
                "id": "qa_what_are_grades",
                "text": "Q: What are the different grades? A: Grades are credit quality tiers ranging from P1 (highest quality) to P6 (lowest quality). Lower grades typically have higher interest rates to compensate for higher risk. P1 represents the best credit quality customers.",
                "metadata": {"type": "qa", "question": "what are grades"}
            },
            {
                "id": "qa_what_is_fico",
                "text": "Q: What is FICO? A: FICO is a credit score ranging from 300 to 850 that indicates creditworthiness. We group FICO scores into bands: <640 (subprime), 640-699 (near-prime), 700-759 (prime), and 760+ (super-prime). Higher FICO scores indicate better credit history and lower risk.",
                "metadata": {"type": "qa", "question": "what is fico"}
            },
            {
                "id": "qa_what_is_repeat_type",
                "text": "Q: What is repeat type? A: Repeat type indicates whether a customer is new or returning. 'New' customers are applying for their first loan with us, while 'Repeat' customers have had previous loans. Repeat customers often have higher approval rates due to established history.",
                "metadata": {"type": "qa", "question": "what is repeat type"}
            },
            {
                "id": "qa_what_is_term",
                "text": "Q: What is loan term? A: Loan term is the length of the loan in months. Common terms are 36, 48, 60, 72, and 84 months. Longer terms have lower monthly payments but result in more total interest paid over the life of the loan.",
                "metadata": {"type": "qa", "question": "what is term"}
            },
            {
                "id": "qa_what_is_apr",
                "text": "Q: What is APR? A: APR (Annual Percentage Rate) is the yearly interest rate charged on the loan. It includes the interest rate plus any fees. Lower APRs are offered to customers with better credit profiles (higher FICO scores, better grades).",
                "metadata": {"type": "qa", "question": "what is apr"}
            },
            {
                "id": "qa_forecast_accuracy",
                "text": "Q: How do we measure forecast accuracy? A: Forecast accuracy is measured by comparing actual issuance to forecasted issuance. We calculate the ratio (actual/forecast) and the delta (actual - forecast). Values above 1.0 or positive deltas indicate we exceeded the forecast.",
                "metadata": {"type": "qa", "question": "how to measure forecast accuracy"}
            },
            {
                "id": "qa_what_is_funnel",
                "text": "Q: What is the customer acquisition funnel? A: The customer acquisition funnel shows the progression from submission to approval to issuance. It helps identify where customers drop off in the process. A typical funnel shows: Submissions → Approvals → Issuances.",
                "metadata": {"type": "qa", "question": "what is funnel"}
            },
            {
                "id": "qa_mom_wow",
                "text": "Q: What is MoM and WoW? A: MoM stands for Month-over-Month comparison, showing the percentage change from the previous month. WoW stands for Week-over-Week comparison, showing the percentage change from the previous week. These metrics help identify trends and changes in performance.",
                "metadata": {"type": "qa", "question": "what is mom and wow"}
            },
            {
                "id": "qa_what_is_prod_type",
                "text": "Q: What are the product types? A: Product types include Prime (for prime credit customers), NP (near-prime for customers with slightly lower credit), and D2P (direct to prime). Each product type has different underwriting criteria and pricing.",
                "metadata": {"type": "qa", "question": "what are product types"}
            },
            {
                "id": "qa_what_is_purpose",
                "text": "Q: What are loan purposes? A: Loan purposes indicate why customers are borrowing. Common purposes include debt_consolidation (most common), home_improvement, major_purchase, medical, car, and other. Debt consolidation loans are used to pay off other debts.",
                "metadata": {"type": "qa", "question": "what are loan purposes"}
            },
            {
                "id": "qa_amount_vs_count",
                "text": "Q: When do metrics refer to amounts vs counts? A: By default, app submits, app approvals, and issuances refer to dollar amounts (total loan amounts). To get counts (number of applications or loans), you must explicitly ask for 'number of' or 'count of'. For example, 'number of app submits' gives you the count.",
                "metadata": {"type": "qa", "question": "amount vs count"}
            },
            {
                "id": "qa_date_columns",
                "text": "Q: What are the different date columns? A: We have several date columns: app_create_d (when application was created), app_submit_d (when submitted), apps_approved_d (when approved), and issued_d (when loan was issued). Each metric uses the appropriate date column for filtering.",
                "metadata": {"type": "qa", "question": "what are date columns"}
            },
            {
                "id": "qa_time_windows",
                "text": "Q: What time windows can I query? A: You can query various time windows including 'last 7 days', 'last full week' (Monday-Sunday), 'last 30 days', 'last full month', and 'last 3 full months'. By default, queries use the last 30 days if not specified.",
                "metadata": {"type": "qa", "question": "what time windows"}
            },
            {
                "id": "qa_granularity",
                "text": "Q: What granularity options are available? A: Data can be aggregated at daily, weekly, or monthly granularity. For time windows of 3 months or less, we default to weekly granularity. For longer periods, we use monthly granularity.",
                "metadata": {"type": "qa", "question": "what granularity options"}
            },
            {
                "id": "qa_segments",
                "text": "Q: What segments can I filter by? A: You can filter data by channel, grade, product type, repeat type, term, FICO band, and purpose. These segments help you analyze specific customer cohorts and identify performance drivers.",
                "metadata": {"type": "qa", "question": "what segments"}
            },
            {
                "id": "qa_drivers",
                "text": "Q: What are drivers? A: Drivers are specific segments that contribute most to overall variance. We identify the top 3 positive drivers (segments with largest increases) and top 3 negative drivers (segments with largest decreases) to help explain changes in performance.",
                "metadata": {"type": "qa", "question": "what are drivers"}
            },
            {
                "id": "qa_omb_channel",
                "text": "Q: What is OMB channel? A: OMB stands for Online Marketing Brand. It's one of our primary digital marketing channels for customer acquisition, typically involving display advertising and brand campaigns.",
                "metadata": {"type": "qa", "question": "what is omb"}
            },
            {
                "id": "qa_d2lc_channel",
                "text": "Q: What is D2LC channel? A: D2LC stands for Direct to Lending Club. It represents customers who come directly to our platform, often through organic search or direct navigation, rather than through paid marketing channels.",
                "metadata": {"type": "qa", "question": "what is d2lc"}
            },
            {
                "id": "qa_conversion_rate",
                "text": "Q: How do I calculate conversion rates? A: Conversion rates show the percentage of customers moving from one funnel stage to the next. For example, approval rate is approvals/offers, and funding rate is issuances/submissions. These help identify bottlenecks in the customer journey.",
                "metadata": {"type": "qa", "question": "how to calculate conversion"}
            },
            {
                "id": "qa_variance_analysis",
                "text": "Q: What is variance analysis? A: Variance analysis compares performance across time periods (MoM or WoW) to identify changes. It includes calculating percentage deltas and identifying which segments are driving the changes. This helps explain why metrics are moving up or down.",
                "metadata": {"type": "qa", "question": "what is variance analysis"}
            },
            {
                "id": "qa_trend_analysis",
                "text": "Q: What is trend analysis? A: Trend analysis shows how metrics change over time, typically displayed as line or area charts. It helps identify patterns, seasonality, and long-term trends in customer acquisition and loan performance.",
                "metadata": {"type": "qa", "question": "what is trend analysis"}
            },
            {
                "id": "qa_distribution_analysis",
                "text": "Q: What is distribution analysis? A: Distribution analysis shows the composition or breakdown of a metric across different segments. For example, showing what percentage of issuances come from each channel or grade. This helps understand the mix of your business.",
                "metadata": {"type": "qa", "question": "what is distribution"}
            },
            {
                "id": "qa_relationship_analysis",
                "text": "Q: What is relationship analysis? A: Relationship analysis examines correlations between two metrics, typically shown as scatter plots. For example, analyzing the relationship between FICO scores and APR, or between loan amount and approval rate.",
                "metadata": {"type": "qa", "question": "what is relationship analysis"}
            },
            {
                "id": "qa_cache",
                "text": "Q: Are query results cached? A: Yes, query results are cached for 10 minutes. If you ask the same question within that time window, you'll get an instant response from the cache. This improves performance for repeated queries.",
                "metadata": {"type": "qa", "question": "are results cached"}
            },
            {
                "id": "qa_export",
                "text": "Q: Can I export data? A: Yes, you can export chart data as CSV files or export visualizations as PNG images. Use the export buttons on chart cards to download data for presentations or further analysis.",
                "metadata": {"type": "qa", "question": "can i export"}
            },
            {
                "id": "qa_filters",
                "text": "Q: How do I apply filters? A: You can apply filters by selecting values from the segment filter dropdowns in the toolbar, or by mentioning segments in your natural language query. For example, 'Show issuances for Email channel' or 'P1 grade approvals'.",
                "metadata": {"type": "qa", "question": "how to apply filters"}
            }
        ]
        
        documents.extend(qa_exemplars)
        
        return documents
    
    def retrieve(self, query: str, k: int = 3) -> List[str]:
        """
        Retrieve relevant documents using semantic search.
        
        Args:
            query: User query for semantic search
            k: Number of top results to return (default: 3)
        
        Returns:
            List of relevant document texts
        """
        # Generate query embedding
        query_embedding = self.embeddings.embed_query(query)
        
        # Query collection
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k
        )
        
        # Extract and return document texts
        if results and results["documents"]:
            return results["documents"][0]
        
        return []
    
    def reset(self):
        """Reset the collection (useful for testing)."""
        try:
            self.client.delete_collection(name=self.collection_name)
            self._initialize_collection()
        except Exception:
            pass


# Singleton instance
_rag_tool_instance = None


def get_rag_tool(persist_directory: str = "./data/chroma") -> RAGTool:
    """
    Get or create singleton RAG tool instance.
    
    Args:
        persist_directory: Path to persistent Chroma storage
    
    Returns:
        RAGTool instance
    """
    global _rag_tool_instance
    
    if _rag_tool_instance is None:
        _rag_tool_instance = RAGTool(persist_directory=persist_directory)
    
    return _rag_tool_instance


def retrieve(query: str, k: int = 3) -> List[str]:
    """
    Convenience function for retrieving documents.
    
    Args:
        query: User query for semantic search
        k: Number of top results to return (default: 3)
    
    Returns:
        List of relevant document texts
    """
    tool = get_rag_tool()
    return tool.retrieve(query, k)
