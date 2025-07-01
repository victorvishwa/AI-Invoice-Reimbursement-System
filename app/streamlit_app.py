import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime
import time
import io
import zipfile

# Page configuration
st.set_page_config(
    page_title="Intelligent Invoice Reimbursement System",
    page_icon="🧾",
    layout="wide"
)

# API configuration
API_BASE_URL = "http://localhost:8000"

def check_api_health():
    """Check if the API is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def get_policy_info():
    """Get information about the integrated policy"""
    try:
        response = requests.get(f"{API_BASE_URL}/analyze-invoices/policy", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except:
        return None

def analyze_invoices(invoices_file, employee_name="Batch Analysis", policy_file=None, use_integrated_policy=True):
    """Send invoice analysis request to API"""
    try:
        files = {'invoices': ('invoices.zip', invoices_file, 'application/zip')}
        data = {'employee_name': employee_name}
        
        # Add policy file if provided
        if policy_file and not use_integrated_policy:
            files['policy'] = ('policy.pdf', policy_file, 'application/pdf')
        
        # Add query parameter for policy type
        params = {'use_integrated_policy': use_integrated_policy}
        
        response = requests.post(
            f"{API_BASE_URL}/analyze-invoices/",
            files=files,
            data=data,
            params=params,
            timeout=300
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

def chat_query(query):
    """Send chat query to API"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/chat-query/",
            json={"query": query},
            timeout=60
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

def main():
    st.title("🧾 Intelligent Invoice Reimbursement System")
    
    # Check API health
    if not check_api_health():
        st.error("⚠️ Backend API is not running. Please start the FastAPI server first.")
        st.info("Run: `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`")
        return
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a page",
        ["Invoice Analysis", "Chat Query", "System Status"]
    )
    
    if page == "Invoice Analysis":
        show_invoice_analysis_page()
    elif page == "Chat Query":
        show_chat_query_page()
    elif page == "System Status":
        show_system_status_page()

def show_invoice_analysis_page():
    st.header("📊 Invoice Analysis")
    
    # Policy selection
    st.subheader("Policy Configuration")
    
    # Get policy info
    policy_info = get_policy_info()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        use_integrated_policy = st.checkbox(
            "Use Integrated IAI Solution Policy", 
            value=True,
            help="Use the built-in IAI Solution Employee Reimbursement Policy"
        )
    
    with col2:
        if policy_info and policy_info.get('status') == 'success':
            policy_data = policy_info.get('policy', {})
            st.info(f"**{policy_data.get('company_name', 'IAI Solution')}**\n"
                   f"Policy Version: {policy_data.get('version', '1.0')}")
    
    # Show policy details if using integrated policy
    if use_integrated_policy and policy_info and policy_info.get('status') == 'success':
        with st.expander("📋 View IAI Solution Policy Details"):
            policy_data = policy_info.get('policy', {})
            st.write(f"**Company:** {policy_data.get('company_name', 'IAI Solution')}")
            st.write(f"**Policy:** {policy_data.get('policy_title', 'Employee Reimbursement Policy')}")
            st.write(f"**Version:** {policy_data.get('version', '1.0')}")
            
            st.subheader("Expense Categories & Limits")
            categories = policy_data.get('categories', {})
            for category_key, category_data in categories.items():
                st.write(f"**{category_data.get('name', category_key)}**")
                st.write(f"  - Limit: ₹{category_data.get('max_amount', 0):.2f}")
                st.write(f"  - Description: {category_data.get('description', 'N/A')}")
                st.write(f"  - Policy Section: {category_data.get('policy_section', 'N/A')}")
                st.write("")
    
    # File upload section
    st.subheader("Upload Files")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if not use_integrated_policy:
            policy_file = st.file_uploader(
                "Upload HR Policy PDF",
                type=['pdf'],
                key="policy_uploader",
                help="Upload your custom HR policy PDF file"
            )
        else:
            st.info("✅ Using integrated IAI Solution policy")
            policy_file = None
    
    with col2:
        invoices_file = st.file_uploader(
            "Upload Invoices ZIP",
            type=['zip'],
            key="invoices_uploader",
            help="Upload a ZIP file containing employee invoice PDFs"
        )
    
    # Analysis button
    if st.button("🚀 Analyze Invoices", type="primary"):
        if not invoices_file:
            st.warning("Please upload invoices ZIP file")
            return
        
        if not use_integrated_policy and not policy_file:
            st.warning("Please upload a policy file when not using integrated policy")
            return
        
        with st.spinner("Analyzing invoices..."):
            result = analyze_invoices(invoices_file, "Batch Analysis", policy_file, use_integrated_policy)
            
            if result:
                show_analysis_results(result)
            else:
                st.error("Analysis failed. Please check your files and try again.")

def show_analysis_results(result):
    st.header("📋 Analysis Results")
    
    # Summary statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Invoices", result.get('total_invoices', 0))
    
    with col2:
        processing_time = result.get('processing_time', 0)
        st.metric("Processing Time", f"{processing_time:.2f}s")
    
    with col3:
        status = result.get('status', 'unknown')
        if status == 'success':
            st.metric("Status", "✅ Success")
        else:
            st.metric("Status", "❌ Error")
    
    with col4:
        # Calculate total amounts
        results = result.get('results', [])
        total_amount = sum(r.get('amount', 0) for r in results if r.get('amount'))
        total_reimbursed = sum(r.get('reimbursed_amount', 0) for r in results if r.get('reimbursed_amount'))
        st.metric("Total Amount", f"₹{total_amount:.2f}")
    
    # Results table
    results = result.get('results', [])
    if results:
        st.subheader("Invoice Details")
        
        # Prepare data for table
        table_data = []
        for r in results:
            table_data.append({
                'Invoice ID': r.get('invoice_id', 'Unknown'),
                'Status': r.get('status', 'Unknown'),
                'Category': r.get('category', 'Unknown'),
                'Reason': r.get('reason', 'No reason provided')[:100] + '...' if len(r.get('reason', '')) > 100 else r.get('reason', 'No reason provided'),
                'Policy Reference': r.get('policy_reference', 'No reference'),
                'Amount': f"₹{r.get('amount', 0):.2f}" if r.get('amount') else 'N/A',
                'Reimbursed': f"₹{r.get('reimbursed_amount', 0):.2f}" if r.get('reimbursed_amount') else 'N/A'
            })
        
        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True)
        
        # Individual invoice details with expandable sections
        st.subheader("📄 Individual Invoice Analysis")
        
        for i, r in enumerate(results, 1):
            with st.expander(f"📋 Invoice {i}: {r.get('invoice_id', 'Unknown')} - {r.get('status', 'Unknown')}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Invoice ID:** {r.get('invoice_id', 'Unknown')}")
                    st.write(f"**Status:** {r.get('status', 'Unknown')}")
                    st.write(f"**Category:** {r.get('category', 'Unknown')}")
                    st.write(f"**Policy Rule:** {r.get('policy_rule', 'Unknown')}")
                
                with col2:
                    amount = r.get('amount', 0)
                    reimbursed = r.get('reimbursed_amount', 0)
                    st.write(f"**Amount:** ₹{amount:.2f}" if amount else "**Amount:** N/A")
                    st.write(f"**Reimbursed:** ₹{reimbursed:.2f}" if reimbursed else "**Reimbursed:** N/A")
                    st.write(f"**Policy Reference:** {r.get('policy_reference', 'No reference')}")
                
                st.write("**Reason:**")
                st.info(r.get('reason', 'No reason provided'))
        
        # Status distribution chart
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Status Distribution")
            status_counts = {}
            for r in results:
                status = r.get('status', 'Unknown')
                status_counts[status] = status_counts.get(status, 0) + 1
            
            if status_counts:
                chart_data = pd.DataFrame(list(status_counts.items()), columns=['Status', 'Count'])
                st.bar_chart(chart_data.set_index('Status'))
        
        with col2:
            st.subheader("Category Distribution")
            category_counts = {}
            for r in results:
                category = r.get('category', 'Unknown')
                category_counts[category] = category_counts.get(category, 0) + 1
            
            if category_counts:
                chart_data = pd.DataFrame(list(category_counts.items()), columns=['Category', 'Count'])
                st.bar_chart(chart_data.set_index('Category'))

def show_chat_query_page():
    st.header("💬 Chat Query")
    
    st.write("Ask questions about previously analyzed invoices using natural language.")
    
    # Chat interface
    st.subheader("Ask a Question")
    
    # Initialize chat history
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    # Initialize chat_query and clear trigger before widget
    if 'chat_query' not in st.session_state:
        st.session_state.chat_query = ""
    if 'clear_chat_query_trigger' not in st.session_state:
        st.session_state.clear_chat_query_trigger = False
    # Clear input if trigger is set (before widget)
    if st.session_state.clear_chat_query_trigger:
        st.session_state.chat_query = ""
        st.session_state.clear_chat_query_trigger = False

    # Chat options
    col1, col2 = st.columns([3, 1])
    
    with col1:
        query = st.text_input(
            "Enter your question:",
            placeholder="e.g., Why was John's invoice rejected in June?",
            key="chat_query"
        )
    
    with col2:
        use_streaming = st.checkbox("Use Streaming", value=True, help="Enable real-time streaming responses")
    
    if st.button("🔍 Search", type="primary"):
        if not query:
            st.warning("Please enter a question")
            return
        
        if use_streaming:
            # Streaming response
            with st.spinner("Searching for relevant information..."):
                result = chat_query(query)
                
                if result:
                    # Create a placeholder for streaming response
                    response_placeholder = st.empty()
                    full_response = ""
                    
                    # Simulate streaming (in a real implementation, this would be actual streaming)
                    response_text = result.get('response', '')
                    words = response_text.split()
                    
                    for i, word in enumerate(words):
                        full_response += word + " "
                        response_placeholder.markdown(f"**Assistant:** {full_response}...")
                        time.sleep(0.05)  # Simulate streaming delay
                    
                    # Final response
                    response_placeholder.markdown(f"**Assistant:** {full_response}")
                    
                    # Add to chat history
                    st.session_state.chat_history.append({
                        'query': query,
                        'response': full_response,
                        'sources': result.get('sources', []),
                        'confidence': result.get('confidence_score', 0.0),
                        'timestamp': datetime.now(),
                        'streaming': True
                    })
                    # Set trigger to clear input and rerun
                    st.session_state.clear_chat_query_trigger = True
                    st.rerun()
        else:
            # Non-streaming response
            with st.spinner("Searching for relevant information..."):
                result = chat_query(query)
                
                if result:
                    # Add to chat history
                    st.session_state.chat_history.append({
                        'query': query,
                        'response': result.get('response', ''),
                        'sources': result.get('sources', []),
                        'confidence': result.get('confidence_score', 0.0),
                        'timestamp': datetime.now(),
                        'streaming': False
                    })
                    # Set trigger to clear input and rerun
                    st.session_state.clear_chat_query_trigger = True
                    st.rerun()
    
    # Display chat history
    if st.session_state.chat_history:
        st.subheader("Chat History")
        
        for i, chat_item in enumerate(reversed(st.session_state.chat_history)):
            st.write(f"**You:** {chat_item['query']}")
            
            # Show streaming indicator if used
            if chat_item.get('streaming', False):
                st.write(f"**Assistant:** {chat_item['response']} 🌊")
            else:
                st.write(f"**Assistant:** {chat_item['response']}")
            
            if chat_item['sources']:
                with st.expander(f"Sources ({len(chat_item['sources'])})"):
                    for source in chat_item['sources']:
                        st.write(f"- Invoice: {source.get('invoice_id', 'Unknown')}")
                        st.write(f"  Employee: {source.get('employee', 'Unknown')}")
                        st.write(f"  Status: {source.get('status', 'Unknown')}")
                        st.write(f"  Similarity: {source.get('similarity_score', 0):.2%}")
            
            st.divider()
    
    # Clear chat history
    if st.session_state.chat_history and st.button("🗑️ Clear Chat History"):
        st.session_state.chat_history = []
        st.rerun()

def show_system_status_page():
    st.header("🔧 System Status")
    
    # Check API health
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            
            st.success("✅ Backend API is running")
            
            # Display health information
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("API Status", health_data.get('status', 'Unknown'))
                st.metric("Version", health_data.get('version', 'Unknown'))
            
            with col2:
                services = health_data.get('services', {})
                st.metric("Database", services.get('database', 'Unknown'))
                st.metric("API Service", services.get('api', 'Unknown'))
            
            # API endpoints
            st.subheader("Available Endpoints")
            endpoints = [
                ("POST", "/analyze-invoices/", "Analyze employee invoices"),
                ("POST", "/chat-query/", "Query past analyses"),
                ("GET", "/health", "System health check"),
                ("GET", "/docs", "API documentation")
            ]
            
            for method, endpoint, description in endpoints:
                st.write(f"**{method}** `{endpoint}` - {description}")
        
        else:
            st.error(f"❌ API returned status code: {response.status_code}")
            
    except Exception as e:
        st.error(f"❌ Cannot connect to API: {str(e)}")
        st.info("Make sure the FastAPI server is running on http://localhost:8000")

if __name__ == "__main__":
    main() 