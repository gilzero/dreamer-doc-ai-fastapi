# app/services/ai_analyzer.py

from openai import AsyncOpenAI
from typing import Dict, Optional, Any
from pathlib import Path
import logging
import json

from app.core.config import get_settings
from app.schemas.document import DocumentAnalysisOptions

settings = get_settings()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


class AnalysisResult:
    def __init__(
            self,
            summary: str,
            character_analysis: Optional[str] = None,
            plot_analysis: Optional[str] = None,
            theme_analysis: Optional[str] = None,
            readability_score: Optional[float] = None,
            sentiment_score: Optional[float] = None,
            style_consistency: Optional[str] = None
    ):
        self.summary = summary
        self.character_analysis = character_analysis
        self.plot_analysis = plot_analysis
        self.theme_analysis = theme_analysis
        self.readability_score = readability_score
        self.sentiment_score = sentiment_score
        self.style_consistency = style_consistency


async def analyze_document(
        file_path: str,
        analysis_options: DocumentAnalysisOptions
) -> AnalysisResult:
    """
    Analyze document using OpenAI's GPT model.
    """
    try:
        # Read document content
        content = await read_document_content(file_path)

        # Build analysis prompt based on options
        system_prompt = create_system_prompt(analysis_options)

        # Log analysis start
        logger.info(f"Starting analysis for document: {file_path}")

        # Make API call to OpenAI
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content}
            ],
            temperature=settings.OPENAI_TEMPERATURE,
            max_tokens=settings.OPENAI_MAX_TOKENS
        )

        # Parse and structure the response
        analysis = parse_openai_response(response.choices[0].message.content)

        # Log analysis completion
        logger.info("Analysis completed successfully")

        return AnalysisResult(**analysis)

    except Exception as e:
        logger.error(f"Error analyzing document: {str(e)}")
        raise


def create_system_prompt(options: DocumentAnalysisOptions) -> str:
    """
    Create system prompt based on analysis options.
    """
    base_prompt = """你是一位专业的文档分析专家。请用中文分析这篇文档，按照以下格式提供JSON输出：

{
    "summary": "3-5句话总结文档要点",
"""

    optional_sections = {
        "character_analysis": options.character_analysis,
        "plot_analysis": options.plot_analysis,
        "theme_analysis": options.theme_analysis,
        "readability_score": options.readability_assessment,
        "sentiment_score": options.sentiment_analysis,
        "style_consistency": options.style_consistency
    }

    for section, enabled in optional_sections.items():
        if enabled:
            if section.endswith('_score'):
                base_prompt += f'    "{section}": "0-100的评分",\n'
            else:
                base_prompt += f'    "{section}": "详细分析",\n'

    base_prompt += "}"

    base_prompt += """

请确保:
1. 输出为有效的JSON格式
2. 分析深入且具体
3. 使用恰当的专业术语
4. 避免笼统的描述
5. 保持客观中立的语气"""

    return base_prompt


async def read_document_content(file_path: str) -> str:
    """
    Read content from document file.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
        content = await f.read()
    return content


def parse_openai_response(response: str) -> Dict[str, Any]:
    """
    Parse and validate OpenAI response.
    """
    try:
        # Clean up response to ensure valid JSON
        cleaned_response = response.strip()
        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:-3]

        # Parse JSON
        analysis = json.loads(cleaned_response)

        # Validate required fields
        if "summary" not in analysis:
            raise ValueError("Response missing required 'summary' field")

        # Convert score strings to floats if present
        for score_field in ['readability_score', 'sentiment_score']:
            if score_field in analysis:
                try:
                    analysis[score_field] = float(analysis[score_field])
                except ValueError:
                    logger.warning(f"Could not convert {score_field} to float")
                    analysis[score_field] = None

        return analysis

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse OpenAI response: {str(e)}")
        logger.error(f"Raw response: {response}")
        raise ValueError("Invalid JSON response from OpenAI")

    except Exception as e:
        logger.error(f"Error parsing OpenAI response: {str(e)}")
        raise


# Optional: Add caching to improve performance
from functools import lru_cache


@lru_cache(maxsize=100)
def get_cached_analysis(file_hash: str) -> Optional[AnalysisResult]:
    """
    Get cached analysis result if available.
    """
    # Implement caching logic here
    return None