import os
from typing import List
import json
import re
from pydantic import BaseModel, Field
from agno.agent import Agent
from agno.models.mistral import MistralChat
from dotenv import load_dotenv

load_dotenv()

class RepositoryContent(BaseModel):
    """Schema for repository content generated by AI"""
    description: str = Field(
        ..., 
        description="A concise description of the repository (max 160 chars)"
    )
    readme_content: str = Field(
        ...,
        description="Complete README content in markdown format"
    )

class RepoContentGenerator:
    def __init__(self):
        model = MistralChat(os.getenv("DEFAULT_MODEL_ID"))
        self.agent = Agent(
            model=model,
            description="A technical writer specialized in creating comprehensive GitHub repository documentation based on PRD content",
            instructions=f"""
            You are a technical documentation expert who creates clear, professional GitHub repository content that accurately reflects PRD specifications.
            
            Your responsibilities:
            1. Analyze PRD documents to extract key project information
            2. Create concise repository descriptions
            3. Generate comprehensive README content that aligns with PRD structure
            4. Present information in a clear, hierarchical manner
            
            Style guide:
            - Use clear, professional language
            - Add relevant emojis for visual organization
            - Follow markdown best practices
            - Use proper markdown headers (# for title, ## for sections)
            - Include tables for structured information where appropriate
            - Use bullet points for lists and requirements
            
            README sections to include (in order):
            # [Project Name]
            1. 🎯 Project Title and Description
               - Brief introduction
               - Project objectives
               - Target completion timeline
            
            2. 👥 Target Users
               - List primary user groups
               - Key user characteristics
               - User requirements
            
            3. 🌟 Key Features
               - List high-priority features
               - Include priority level
               - Brief description of each feature
               - User stories or acceptance criteria if provided
            
            4. 🔧 Technical Overview
               - Architecture components
               - Technology stack
               - Infrastructure requirements
            
            5. ⚙️ Non-Functional Requirements
               - Performance metrics
               - Security requirements
               - Scalability requirements
               - Other relevant NFRs from PRD
            
            6. 📊 Project Scope
               - Budget information (if public)
               - Team composition
               - Project timeline
               - Key limitations or constraints
            
            7. ✅ Acceptance Criteria
               - Key success metrics
               - Required certifications
               - Testing requirements
            
            Important guidelines:
            - Include ONLY information present in the PRD
            - Maintain the same level of detail as the PRD
            - Keep technical specifications if mentioned
            - Exclude implementation details unless specified in PRD
            - Do NOT add speculative information
            - Do NOT include setup/installation unless in PRD
            
            Required Output Format:
            You must respond with a JSON object that matches this Pydantic model schema:
            {RepositoryContent.model_json_schema()}
            
            Focus on information valuable to stakeholders and project starters.
            Include ONLY information that is present in the PRD.
            Do NOT include setup, usage, license, or contact information.
            """,
            show_tool_calls=True,
            markdown=True,
            debug_mode=True,
        )

    def extract_json_from_response(self, response_content: str) -> str:
        """Extract JSON content from markdown code blocks"""
        json_matches = list(re.finditer(r"```(?:json)?([\s\S]*?)```", response_content, re.MULTILINE))
        if json_matches:
            # Use the last match
            return json_matches[-1].group(1).strip()
        return response_content.strip()

    def generate_content(self, repo_name: str, prd_content: str) -> RepositoryContent:
        """Generate repository content from PRD"""
        prompt = f"""
        Please analyze this PRD and generate stakeholder-focused repository content for '{repo_name}':
        ```markdown
        {prd_content}
        ```
        """

        response = self.agent.run(prompt)
        if not response or not response.content:
            raise ValueError("Failed to generate repository content")
            
        try:
            # Parse the JSON response
            if isinstance(response.content, str):
                # Extract JSON from markdown code blocks if present
                json_content = self.extract_json_from_response(response.content)
                content_dict = json.loads(json_content)
                return RepositoryContent(**content_dict)
            elif isinstance(response.content, RepositoryContent):
                return response.content
            else:
                raise ValueError(f"Unexpected response type: {type(response.content)}")
        except Exception as e:
            raise ValueError(f"Failed to parse agent response: {str(e)}")

    def format_readme(self, repo_name: str, content: RepositoryContent) -> str:
        """Return the README content directly since it's already formatted"""
        return content.readme_content 