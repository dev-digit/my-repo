"""
Test suite for conversation modes
"""

import pytest
from app.modes import CreativeMode, PreciseMode, TeachMode, CodeMode, AnalyzeMode


class TestBaseMode:
    """Test base mode functionality"""

    def test_mode_metadata(self):
        """Test that all modes have required metadata"""
        modes = [
            CreativeMode(),
            PreciseMode(),
            TeachMode(),
            CodeMode(),
            AnalyzeMode()
        ]

        for mode in modes:
            metadata = mode.get_metadata()

            # Check required fields
            assert "name" in metadata
            assert "description" in metadata
            assert "capabilities" in metadata
            assert "recommended_models" in metadata
            assert "temperature_range" in metadata
            assert "max_tokens_suggestion" in metadata

            # Check data types
            assert isinstance(metadata["name"], str)
            assert isinstance(metadata["description"], str)
            assert isinstance(metadata["capabilities"], list)
            assert isinstance(metadata["recommended_models"], list)
            assert isinstance(metadata["temperature_range"], tuple)
            assert isinstance(metadata["max_tokens_suggestion"], int)

    def test_mode_names_unique(self):
        """Test that all mode names are unique"""
        modes = [
            CreativeMode(),
            PreciseMode(),
            TeachMode(),
            CodeMode(),
            AnalyzeMode()
        ]

        names = [mode.name for mode in modes]
        assert len(names) == len(set(names)), "Mode names should be unique"


class TestCreativeMode:
    """Test creative mode functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.mode = CreativeMode()

    def test_system_prompt_generation(self):
        """Test system prompt generation"""
        prompt = self.mode.get_system_prompt()
        assert "creative" in prompt.lower()
        assert "imaginative" in prompt.lower()
        assert len(prompt) > 100

    def test_context_specific_prompt(self):
        """Test context-specific prompt generation"""
        # Test writing context
        prompt = self.mode.get_system_prompt({"topic": "writing"})
        assert "narrative" in prompt.lower()

        # Test brainstorming context
        prompt = self.mode.get_system_prompt({"topic": "brainstorming"})
        assert "ideas" in prompt.lower()

    def test_response_processing(self):
        """Test response processing"""
        formal_response = "Therefore, we can conclude that this is a good idea."
        processed = self.mode.process_response(formal_response)

        # Should add creative flair
        assert "imagine" in processed.lower() or "creative" in processed.lower()

    def test_prompt_enhancement(self):
        """Test prompt enhancement"""
        basic_prompt = "Tell me about space"
        enhanced = self.mode.enhance_prompt(basic_prompt)

        # Should add creative framing
        assert "creatively" in enhanced.lower() or "explore" in enhanced.lower()

    def test_response_validation(self):
        """Test response validation"""
        # Valid response
        valid_response = "Here's a creative story about space travel..."
        assert self.mode.validate_response(valid_response) is True

        # Too short response
        short_response = "Ok"
        assert self.mode.validate_response(short_response) is False

        # Empty response
        empty_response = ""
        assert self.mode.validate_response(empty_response) is False


class TestPreciseMode:
    """Test precise mode functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.mode = PreciseMode()

    def test_system_prompt_generation(self):
        """Test system prompt generation"""
        prompt = self.mode.get_system_prompt()
        assert "precise" in prompt.lower()
        assert "accurate" in prompt.lower()
        assert "factual" in prompt.lower()

    def test_context_specific_prompt(self):
        """Test context-specific prompt generation"""
        # Test science context
        prompt = self.mode.get_system_prompt({"topic": "science"})
        assert "scientific" in prompt.lower()

    def test_response_processing(self):
        """Test response processing"""
        uncertain_response = "I think that maybe this could work..."
        processed = self.mode.process_response(uncertain_response)

        # Should reduce uncertainty
        assert "I think" not in processed or "based on" in processed.lower()

    def test_prompt_enhancement(self):
        """Test prompt enhancement"""
        basic_prompt = "What is photosynthesis?"
        enhanced = self.mode.enhance_prompt(basic_prompt)

        # Should add precision focus
        assert "precise" in enhanced.lower() or "accurate" in enhanced.lower()

    def test_response_validation(self):
        """Test response validation"""
        # Valid response with data
        valid_response = "Photosynthesis is the process by which plants convert sunlight into energy."
        assert self.mode.validate_response(valid_response) is True

        # Too speculative response
        speculative_response = "Maybe perhaps it might work sometimes I think."
        assert self.mode.validate_response(speculative_response) is False


class TestTeachMode:
    """Test teach mode functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.mode = TeachMode()

    def test_system_prompt_generation(self):
        """Test system prompt generation"""
        prompt = self.mode.get_system_prompt()
        assert "teach" in prompt.lower()
        assert "explain" in prompt.lower()
        assert "step by step" in prompt.lower()

    def test_context_specific_prompt(self):
        """Test context-specific prompt generation"""
        # Test beginner level
        prompt = self.mode.get_system_prompt({"level": "beginner"})
        assert "simple" in prompt.lower()

        # Test math topic
        prompt = self.mode.get_system_prompt({"topic": "math", "level": "beginner"})
        assert "calculations" in prompt.lower()

    def test_response_processing(self):
        """Test response processing"""
        basic_response = "This is how it works."
        processed = self.mode.process_response(basic_response)

        # Should add educational structure
        assert "step" in processed.lower() or "first" in processed.lower() or len(processed) > len(basic_response)

    def test_prompt_enhancement(self):
        """Test prompt enhancement"""
        basic_prompt = "Python"
        enhanced = self.mode.enhance_prompt(basic_prompt)

        # Should add educational framing
        assert "teach" in enhanced.lower() or "explain" in enhanced.lower()

    def test_response_validation(self):
        """Test response validation"""
        # Good educational response
        valid_response = "Let me break this down step by step. First, we need to..."
        assert self.mode.validate_response(valid_response) is True

        # Non-educational response
        non_educational = "It works."
        assert self.mode.validate_response(non_educational) is False


class TestCodeMode:
    """Test code mode functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.mode = CodeMode()

    def test_system_prompt_generation(self):
        """Test system prompt generation"""
        prompt = self.mode.get_system_prompt()
        assert "code" in prompt.lower()
        assert "programming" in prompt.lower()
        assert "examples" in prompt.lower()

    def test_context_specific_prompt(self):
        """Test context-specific prompt generation"""
        # Test Python language
        prompt = self.mode.get_system_prompt({"language": "python"})
        assert "python" in prompt.lower()

        # Test debugging task
        prompt = self.mode.get_system_prompt({"task_type": "debugging"})
        assert "debugging" in prompt.lower()

    def test_response_processing(self):
        """Test response processing"""
        code_response = "def hello(): print('hello')"
        processed = self.mode.process_response(code_response)

        # Should format code blocks
        assert "```" in processed or "python" in processed.lower()

    def test_prompt_enhancement(self):
        """Test prompt enhancement"""
        basic_prompt = "sort a list"
        enhanced = self.mode.enhance_prompt(basic_prompt)

        # Should add code context
        assert "language" in enhanced.lower() or "code" in enhanced.lower()

    def test_response_validation(self):
        """Test response validation"""
        # Response with code
        code_response = "Here's the function: def sort_list(lst): return sorted(lst)"
        assert self.mode.validate_response(code_response) is True

        # Response without code
        no_code_response = "You should sort the list."
        assert self.mode.validate_response(no_code_response) is False


class TestAnalyzeMode:
    """Test analyze mode functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.mode = AnalyzeMode()

    def test_system_prompt_generation(self):
        """Test system prompt generation"""
        prompt = self.mode.get_system_prompt()
        assert "analyze" in prompt.lower()
        assert "structured" in prompt.lower()
        assert "balanced" in prompt.lower()

    def test_context_specific_prompt(self):
        """Test context-specific prompt generation"""
        # Test comparison analysis
        prompt = self.mode.get_system_prompt({"analysis_type": "comparison"})
        assert "comparison" in prompt.lower()

    def test_response_processing(self):
        """Test response processing"""
        basic_response = "Here are the pros and cons."
        processed = self.mode.process_response(basic_response)

        # Should add structure
        assert "##" in processed or "conclusion" in processed.lower()

    def test_prompt_enhancement(self):
        """Test prompt enhancement"""
        basic_prompt = "compare two options"
        enhanced = self.mode.enhance_prompt(basic_prompt)

        # Should add analytical framing
        assert "analyze" in enhanced.lower() or "structured" in enhanced.lower()

    def test_response_validation(self):
        """Test response validation"""
        # Good analytical response
        valid_response = "When comparing these options, we need to consider several factors. However, there are trade-offs."
        assert self.mode.validate_response(valid_response) is True

        # Non-analytical response
        non_analytical = "This is good."
        assert self.mode.validate_response(non_analytical) is False


if __name__ == "__main__":
    pytest.main([__file__])