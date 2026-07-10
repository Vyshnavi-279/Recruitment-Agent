import streamlit as st

def apply_claymorphism_theme():
    """Injects high-end glassmorphic/claymorphic styling into the Streamlit DOM."""
    st.markdown(
        """
        <style>
        /* Base Background Canvas */
        .stApp {
            background: linear-gradient(135deg, #2b263f 0%, #483b5c 50%, #6d4d54 100%) !important;
            color: #f3eff5 !important;
            font-family: 'Inter', sans-serif;
        }

        /* Claymorphic Rounded Cards */
        .clay-card {
            background: rgba(255, 255, 255, 0.07);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border-radius: 24px;
            border: 1px solid rgba(255, 255, 255, 0.15);
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 
                inset 4px 4px 8px rgba(255, 255, 255, 0.1),
                inset -4px -4px 8px rgba(0, 0, 0, 0.2),
                8px 8px 24px rgba(0, 0, 0, 0.3);
            transition: all 0.3s ease;
        }
        
        .clay-card:hover {
            transform: translateY(-2px);
            box-shadow: 
                inset 6px 6px 12px rgba(255, 255, 255, 0.15),
                inset -6px -6px 12px rgba(0, 0, 0, 0.25),
                12px 12px 32px rgba(0, 0, 0, 0.4);
        }

        /* Soft Volumetric Spherical Badges */
        .clay-badge {
            background: linear-gradient(145deg, #a78bfa, #7c3aed);
            border-radius: 50%;
            width: 48px;
            height: 48px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            color: white;
            box-shadow: 
                inset 3px 3px 6px rgba(255, 255, 255, 0.4),
                inset -3px -3px 6px rgba(0, 0, 0, 0.3),
                4px 4px 12px rgba(0, 0, 0, 0.3);
        }

        /* Futuristic Glowing Dynamic Buttons */
        div.stButton > button:first-child {
            background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 99%, #fecfef 100%) !important;
            color: #312e81 !important;
            border: none !important;
            border-radius: 16px !important;
            padding: 12px 28px !important;
            font-weight: 700 !important;
            box-shadow: 
                inset 2px 2px 4px rgba(255, 255, 255, 0.5),
                inset -2px -2px 4px rgba(0, 0, 0, 0.2),
                0px 8px 16px rgba(255, 154, 158, 0.4) !important;
            transition: all 0.2s ease-in-out !important;
        }

        div.stButton > button:first-child:hover {
            transform: scale(1.03) !important;
            box-shadow: 
                inset 3px 3px 6px rgba(255, 255, 255, 0.6),
                0px 12px 24px rgba(255, 154, 158, 0.6) !important;
        }
        
        /* Glass Style Input Elements */
        .stTextArea textarea, .stFileUploader section {
            background: rgba(255, 255, 255, 0.05) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 16px !important;
            color: #ffffff !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )