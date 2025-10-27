"""
Sprint Report Assistant - Streamlit UI
AI-powered Q&A system for UN-Habitat sprint reports
"""
import streamlit as st
import os
from src.agent import BedrockAgent

# Page config
st.set_page_config(
    page_title="Sprint Report Assistant",
    page_icon="📊",
    layout="centered"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .user-message {
        background-color: #e3f2fd;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .assistant-message {
        background-color: #f5f5f5;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'agent' not in st.session_state:
    try:
        st.session_state.agent = BedrockAgent()
        st.session_state.agent_ready = True
    except Exception as e:
        st.session_state.agent_ready = False
        st.session_state.agent_error = str(e)

# Header
st.markdown('<h1 class="main-header">📊 Sprint Report Assistant</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Ask questions about UN-Habitat QOLI sprint reports</p>', unsafe_allow_html=True)

# Check if vector store exists
if not os.path.exists("./chroma_db"):
    st.error("⚠️ Vector store not found. Please run the setup first:")
    st.code("python src/embeddings.py", language="bash")
    st.stop()

# Check agent status
if not st.session_state.agent_ready:
    st.error(f"⚠️ Error initializing agent: {st.session_state.get('agent_error', 'Unknown error')}")
    st.info("Make sure AWS credentials are configured: `aws configure`")
    st.stop()

# Sidebar
with st.sidebar:
    st.markdown("### ℹ️ About")
    st.markdown("""
    This assistant uses:
    - **Amazon Bedrock** (Titan models)
    - **RAG** (Retrieval Augmented Generation)
    - **Vector Search** (Chroma DB)
    
    Built for analyzing sprint reports from the UN-Habitat Quality of Life Initiative.
    """)
    
    st.markdown("---")
    st.markdown("### 💡 Example Questions")
    st.markdown("""
    - What were the key accomplishments in Q1?
    - Summarize sprint_report_2024_06.pdf
    - What challenges did the team face?
    - What are the velocity trends?
    """)
    
    st.markdown("---")
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# Display chat history
for message in st.session_state.messages:
    if message["role"] == "user":
        st.markdown(f"""
        <div class="user-message">
            <strong>You:</strong><br>
            {message["content"]}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="assistant-message">
            <strong>Assistant:</strong><br>
            {message["content"]}
        </div>
        """, unsafe_allow_html=True)

# Chat input
if prompt := st.chat_input("Ask a question about the sprint reports..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    st.markdown(f"""
    <div class="user-message">
        <strong>You:</strong><br>
        {prompt}
    </div>
    """, unsafe_allow_html=True)
    
    # Get response
    with st.spinner("Thinking..."):
        try:
            response = st.session_state.agent.query(prompt)
            st.session_state.messages.append({"role": "assistant", "content": response})
            
            # Display assistant message
            st.markdown(f"""
            <div class="assistant-message">
                <strong>Assistant:</strong><br>
                {response}
            </div>
            """, unsafe_allow_html=True)
            
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
            st.error(error_msg)
    
    st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.9rem;">
    Built by Anmol Manchanda | <a href="https://github.com/anmolmanchanda">GitHub</a> | <a href="https://anmol.am">Portfolio</a>
</div>
""", unsafe_allow_html=True)
