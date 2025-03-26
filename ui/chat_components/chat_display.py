"""
Chat display module for rendering and styling chat messages using WebEngine.
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, pyqtSlot, Qt
from PyQt5.QtGui import QFont
import os
import json

from ui.chat_components.message_formatter import MessageFormatter


class ChatBubbleDisplay(QWidget):
    """Chat display with bubble styling for messages using WebEngine."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.formatter = MessageFormatter()
        self.chat_history = []
    
    def init_ui(self):
        """Initialize the UI."""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create web view
        self.web_view = QWebEngineView()
        self.web_view.setContextMenuPolicy(Qt.NoContextMenu)  # Disable right-click menu
        
        # Add web view to layout
        layout.addWidget(self.web_view)
    
    def get_html_content(self, chat_history=None):
        """Generate HTML content for the chat display.
        
        Args:
            chat_history: Optional list of ChatMessage objects. If None, use current history.
            
        Returns:
            HTML content as string.
        """
        history = chat_history if chat_history is not None else self.chat_history
        
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                :root {
                    --user-color: #E3F2FD;
                    --assistant-color: #4285F4;
                    --background-color: #F5F5F5;
                    --timestamp-color: #999999;
                    --code-bg-user: rgba(0,0,0,0.07);
                    --code-bg-assistant: rgba(255,255,255,0.15);
                }
                
                * {
                    box-sizing: border-box;
                    margin: 0;
                    padding: 0;
                }
                
                body {
                    font-family: 'Segoe UI', Arial, sans-serif;
                    background-color: var(--background-color);
                    padding: 16px;
                    line-height: 1.5;
                    overflow-y: auto;
                }
                
                .chat-container {
                    max-width: 100%;
                    margin: 0 auto;
                }
                
                .message-group {
                    margin-bottom: 24px;
                    clear: both;
                    width: 100%;
                    overflow: hidden;
                }
                
                .message {
                    max-width: 80%;
                    padding: 12px 16px;
                    border-radius: 18px;
                    margin-bottom: 4px;
                    position: relative;
                    box-shadow: 0 1px 2px rgba(0,0,0,0.1);
                    overflow-wrap: break-word;
                    word-wrap: break-word;
                    word-break: break-word;
                    clear: both;
                }
                
                .message p {
                    margin: 0 0 8px 0;
                }
                
                .message p:last-child {
                    margin-bottom: 0;
                }
                
                .user {
                    float: right;
                    background-color: var(--user-color);
                    color: #000000;
                    border-bottom-right-radius: 4px;
                }
                
                .user:after {
                    content: "";
                    position: absolute;
                    bottom: 0;
                    right: -8px;
                    width: 16px;
                    height: 16px;
                    background-color: var(--user-color);
                    border-bottom-left-radius: 16px;
                    clip-path: polygon(0 0, 0% 100%, 100% 100%);
                }
                
                .assistant {
                    float: left;
                    background-color: var(--assistant-color);
                    color: #FFFFFF;
                    border-bottom-left-radius: 4px;
                }
                
                .assistant:after {
                    content: "";
                    position: absolute;
                    bottom: 0;
                    left: -8px;
                    width: 16px;
                    height: 16px;
                    background-color: var(--assistant-color);
                    border-bottom-right-radius: 16px;
                    clip-path: polygon(0 100%, 100% 0, 100% 100%);
                }
                
                .timestamp {
                    font-size: 10px;
                    color: var(--timestamp-color);
                    margin-top: 4px;
                    margin-bottom: 8px;
                    opacity: 0.8;
                    clear: both;
                }
                
                .timestamp.user {
                    float: right;
                    background: none;
                    box-shadow: none;
                    padding: 0;
                    margin-right: 8px;
                    text-align: right;
                }
                
                .timestamp.user:after {
                    display: none;
                }
                
                .timestamp.assistant {
                    float: left;
                    background: none;
                    box-shadow: none;
                    padding: 0;
                    margin-left: 8px;
                    text-align: left;
                }
                
                .timestamp.assistant:after {
                    display: none;
                }
                
                .code-block {
                    font-family: 'Consolas', 'Monaco', monospace;
                    font-size: 12px;
                    line-height: 1.4;
                    white-space: pre-wrap;
                    padding: 10px;
                    margin: 8px 0;
                    border-radius: 6px;
                    overflow-x: auto;
                }
                
                .user .code-block {
                    background-color: var(--code-bg-user);
                    border-left: 3px solid rgba(0,0,0,0.2);
                    color: #333333;
                }
                
                .assistant .code-block {
                    background-color: var(--code-bg-assistant);
                    border-left: 3px solid rgba(255,255,255,0.3);
                    color: #FFFFFF;
                }
                
                a {
                    color: inherit;
                    text-decoration: underline;
                }
                
                .message-container {
                    width: 100%;
                    overflow: hidden;
                }
                
                .message-tail-spacer {
                    width: 16px;
                    height: 1px;
                    display: inline-block;
                }
            </style>
        </head>
        <body>
            <div class="chat-container" id="chat-container">
        """
        
        # Process chat history
        current_role = None
        
        for i, message in enumerate(history):
            # Check if this is a new message group
            if current_role != message.role:
                # Start new group
                if i > 0:
                    html += "</div>"  # Close previous group
                
                current_role = message.role
                html += f'<div class="message-group">'
            
            # Format message content
            content = MessageFormatter.format_message_content(message.content)
            timestamp = message.timestamp.strftime("%H:%M")
            
            # Create message container
            html += '<div class="message-container">'
            
            # Add message and timestamp based on role
            if message.role == "user":
                html += f'<div class="message user">{content}</div>'
                html += f'<div class="timestamp user">{timestamp}</div>'
            else:
                html += f'<div class="message assistant">{content}</div>'
                html += f'<div class="timestamp assistant">{timestamp}</div>'
            
            # Close message container
            html += '</div>'
        
        # Close any open groups
        if history:
            html += "</div>"
        
        # Complete HTML
        html += """
            </div>
            <script>
                // Scroll to bottom on load
                window.onload = function() {
                    window.scrollTo(0, document.body.scrollHeight);
                };
            </script>
        </body>
        </html>
        """
        
        return html
    
    def refresh_display(self, chat_history=None):
        """Refresh the chat display with message history.
        
        Args:
            chat_history: List of ChatMessage objects. If None, use current history.
        """
        # Store chat history if provided
        if chat_history is not None:
            self.chat_history = chat_history
            
        # Generate HTML content
        html_content = self.get_html_content()
        
        # Set HTML content and scroll to bottom
        self.web_view.setHtml(html_content)
    
    def add_message(self, message):
        """Add a single message to the display.
        
        Args:
            message: ChatMessage object.
        """
        # Add message to history
        self.chat_history.append(message)
        
        # Refresh display
        self.refresh_display() 