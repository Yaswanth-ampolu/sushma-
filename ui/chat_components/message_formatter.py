"""
Message formatter module for handling chat message formatting.
"""
import re


class MessageFormatter:
    """Handles the formatting of chat messages."""

    # Common code patterns to detect code blocks
    CODE_PATTERNS = [
        r'^\s*(def|class|function|var|const|let|import|from|package|public|private)',
        r'^\s*(if|for|while|switch|case|return|try|catch|finally)',
        r'^\s*(```|def |class |function |public |private )',
        r'^\s*\w+\s*\(\w*\)\s*[{:]',  # Function calls or definitions
        r'^\s*<\w+.*>',  # HTML tags
    ]

    @staticmethod
    def format_message_content(content):
        """Format message content with special handling for code blocks and line breaks.
        
        Args:
            content: Raw message content
            
        Returns:
            Formatted HTML content
        """
        # Check for fenced code blocks first (```code```)
        fenced_pattern = r'```(?:\w+)?\n?(.*?)\n?```'
        parts = []
        last_end = 0
        
        for match in re.finditer(fenced_pattern, content, re.DOTALL):
            # Add text before the code block
            if match.start() > last_end:
                text_part = content[last_end:match.start()]
                parts.append(MessageFormatter._format_regular_text(text_part))
            
            # Add the code block
            code_content = match.group(1)
            parts.append(f'<div class="code-block">{MessageFormatter._format_code(code_content)}</div>')
            last_end = match.end()
        
        # Add remaining text
        if last_end < len(content):
            text_part = content[last_end:]
            parts.append(MessageFormatter._process_regular_text(text_part))
        
        # If no fenced code blocks were found, process the entire text
        if not parts:
            parts = [MessageFormatter._process_regular_text(content)]
        
        return "".join(parts)
    
    @staticmethod
    def _process_regular_text(text):
        """Process text without fenced code blocks."""
        lines = text.split('\n')
        
        # Check for code blocks (lines starting with spaces or tabs)
        formatted_parts = []
        in_code_block = False
        code_block_content = []
        
        for line in lines:
            # Detect code based on indentation and common code patterns
            is_code_line = line.startswith('    ') or line.startswith('\t')
            
            # Check against code patterns
            if not is_code_line and line.strip():
                for pattern in MessageFormatter.CODE_PATTERNS:
                    if re.match(pattern, line):
                        is_code_line = True
                        break
            
            if is_code_line:
                if not in_code_block:
                    in_code_block = True
                code_block_content.append(line)
            else:
                # If we were in a code block, close it
                if in_code_block:
                    code_html = '<div class="code-block">' + MessageFormatter._format_code("\n".join(code_block_content)) + '</div>'
                    formatted_parts.append(code_html)
                    code_block_content = []
                    in_code_block = False
                
                # Regular text content
                if line.strip():
                    # Format the line
                    formatted_line = MessageFormatter._format_regular_text(line)
                    formatted_parts.append(f'<p>{formatted_line}</p>')
                else:
                    # Add empty line - in HTML paragraphs provide spacing
                    if formatted_parts and not formatted_parts[-1].endswith('</p>'):
                        formatted_parts.append('<p></p>')
        
        # Close any remaining code block
        if in_code_block:
            code_html = '<div class="code-block">' + MessageFormatter._format_code("\n".join(code_block_content)) + '</div>'
            formatted_parts.append(code_html)
        
        # Join everything back
        return "".join(formatted_parts)
    
    @staticmethod
    def _format_regular_text(text):
        """Format regular text with HTML escaping and basic formatting."""
        # Escape HTML special characters
        text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        # Convert URLs to clickable links
        url_pattern = r'(https?://\S+)'
        text = re.sub(url_pattern, r'<a href="\1" target="_blank">\1</a>', text)
        
        # Handle bold text with * or **
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', text)
        
        return text
    
    @staticmethod
    def _format_code(code_text):
        """Format code text with basic syntax highlighting classes."""
        # Escape HTML special characters
        code_text = code_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        # Apply syntax highlighting to common programming elements
        # Keywords
        keywords = ['function', 'var', 'let', 'const', 'if', 'else', 'for', 'while', 
                   'return', 'class', 'def', 'import', 'from', 'public', 'private', 
                   'protected', 'static', 'new', 'try', 'catch', 'finally', 'throw']
        
        # Create a pattern from keywords
        keyword_pattern = r'\b(' + '|'.join(keywords) + r')\b'
        
        # Apply highlighting
        code_text = re.sub(keyword_pattern, r'<span style="color:#D500F9;">\1</span>', code_text)
        
        # Replace spaces at beginning of lines with non-breaking spaces to preserve indentation
        lines = code_text.split('\n')
        for i, line in enumerate(lines):
            # Count leading spaces
            leading_space_count = len(line) - len(line.lstrip(' '))
            if leading_space_count > 0:
                lines[i] = '&nbsp;' * leading_space_count + line[leading_space_count:]
        
        return '<br>'.join(lines) 