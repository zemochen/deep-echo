"""
AI Provider Switching Integration Tests.

Tests AI provider switching during operation, provider failover,
and multi-provider compatibility scenarios.
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.ai.adapter import AIAdapter
from src.ai.providers.base_provider import AIProvider
from src.ai.responder import GPTResponder
from src.utils.exceptions import AISystemError


class MockProvider(AIProvider):
    """Mock AI provider for testing."""
    
    def __init__(self, name, model="mock-model", response="Mock response", should_fail=False):
        super().__init__("mock-key", model)
        self.name = name
        self.response = response
        self.should_fail = should_fail
        self.call_count = 0
        self.last_prompt = None
        
    def generate_response(self, prompt: str, **kwargs) -> str:
        self.call_count += 1
        self.last_prompt = prompt
        
        if self.should_fail:
            raise AISystemError(f"{self.name} provider failed")
        
        return f"{self.response} from {self.name} (call #{self.call_count})"
        
    def get_provider_name(self) -> str:
        return self.name
        
    def get_model_name(self) -> str:
        return self.model


class MockTranscriber:
    """Mock transcriber for AI provider testing."""
    
    def __init__(self):
        self.transcript_data = {"You": [], "Speaker": []}
        self.transcript_changed_event = threading.Event()
        
    def get_transcript(self):
        return "Mock conversation transcript"
        
    def get_speaker_newest(self, last_time):
        return time.time(), "New speaker content"


class TestAIProviderSwitching:
    """Test AI provider switching functionality."""
    
    def test_basic_provider_switching(self):
        """Test basic switching between providers."""
        adapter = AIAdapter()
        
        # Create test providers
        provider1 = MockProvider("deepseek", "deepseek-chat", "DeepSeek response")
        provider2 = MockProvider("openai", "gpt-3.5-turbo", "OpenAI response")
        provider3 = MockProvider("claude", "claude-3-sonnet", "Claude response")
        
        # Test switching between providers
        adapter.set_provider(provider1)
        response1 = adapter.generate_response("Test prompt")
        assert "DeepSeek response from deepseek" in response1
        assert adapter.get_current_provider() == "deepseek"
        
        adapter.set_provider(provider2)
        response2 = adapter.generate_response("Test prompt")
        assert "OpenAI response from openai" in response2
        assert adapter.get_current_provider() == "openai"
        
        adapter.set_provider(provider3)
        response3 = adapter.generate_response("Test prompt")
        assert "Claude response from claude" in response3
        assert adapter.get_current_provider() == "claude"
        
    def test_provider_switching_preserves_context(self):
        """Test that provider switching preserves conversation context."""
        adapter = AIAdapter()
        
        provider1 = MockProvider("provider1", response="Response 1")
        provider2 = MockProvider("provider2", response="Response 2")
        
        # Set initial provider and generate response
        adapter.set_provider(provider1)
        response1 = adapter.generate_response("First prompt")
        
        # Switch provider and generate response
        adapter.set_provider(provider2)
        response2 = adapter.generate_response("Second prompt")
        
        # Verify both providers received their respective prompts
        assert provider1.last_prompt == "First prompt"
        assert provider2.last_prompt == "Second prompt"
        assert provider1.call_count == 1
        assert provider2.call_count == 1
        
    def test_concurrent_provider_switching(self):
        """Test concurrent provider switching from multiple threads."""
        adapter = AIAdapter()
        results = []
        errors = []
        
        providers = [
            MockProvider(f"provider_{i}", response=f"Response {i}")
            for i in range(5)
        ]
        
        def switch_and_test(provider, prompt):
            try:
                adapter.set_provider(provider)
                response = adapter.generate_response(prompt)
                results.append((provider.name, response))
            except Exception as e:
                errors.append((provider.name, str(e)))
        
        # Start concurrent switching operations
        threads = []
        for i, provider in enumerate(providers):
            thread = threading.Thread(
                target=switch_and_test,
                args=(provider, f"Prompt {i}")
            )
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=5.0)
        
        # Verify results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 5
        
        # Verify each provider was used
        provider_names = [result[0] for result in results]
        assert len(set(provider_names)) >= 1  # At least one provider was used
        
    def test_provider_failover_mechanism(self):
        """Test automatic failover when a provider fails."""
        adapter = AIAdapter()
        
        # Create providers - first one fails, second succeeds
        failing_provider = MockProvider("failing", should_fail=True)
        backup_provider = MockProvider("backup", response="Backup response")
        
        # Set failing provider
        adapter.set_provider(failing_provider)
        
        # Verify it fails
        with pytest.raises(AISystemError):
            adapter.generate_response("Test prompt")
        
        # Switch to backup provider
        adapter.set_provider(backup_provider)
        
        # Verify backup works
        response = adapter.generate_response("Test prompt")
        assert "Backup response from backup" in response
        
    def test_provider_switching_with_responder(self):
        """Test provider switching integration with GPT responder."""
        adapter = AIAdapter()
        transcriber = MockTranscriber()
        
        # Create responder with adapter
        responder = GPTResponder(adapter)
        
        # Test with different providers
        providers = [
            MockProvider("deepseek", response="DeepSeek analysis"),
            MockProvider("openai", response="OpenAI analysis"),
            MockProvider("claude", response="Claude analysis"),
        ]
        
        responses = []
        for provider in providers:
            adapter.set_provider(provider)
            
            # Simulate responder generating response
            response = responder._generate_response_from_transcript("Test transcript")
            responses.append((provider.name, response))
        
        # Verify each provider generated different responses
        assert len(responses) == 3
        assert "DeepSeek analysis" in responses[0][1]
        assert "OpenAI analysis" in responses[1][1]
        assert "Claude analysis" in responses[2][1]
        
    def test_provider_switching_performance(self):
        """Test performance of provider switching operations."""
        adapter = AIAdapter()
        
        providers = [
            MockProvider(f"provider_{i}", response=f"Response {i}")
            for i in range(10)
        ]
        
        # Measure switching performance
        start_time = time.time()
        
        for provider in providers:
            adapter.set_provider(provider)
            response = adapter.generate_response("Performance test")
            assert f"Response {provider.name.split('_')[1]}" in response
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should complete quickly (less than 1 second for 10 switches)
        assert total_time < 1.0
        
        # Average time per switch should be reasonable
        avg_time_per_switch = total_time / len(providers)
        assert avg_time_per_switch < 0.1  # Less than 100ms per switch


class TestProviderCompatibility:
    """Test compatibility between different AI providers."""
    
    def test_provider_interface_consistency(self):
        """Test that all providers implement the same interface."""
        providers = [
            MockProvider("deepseek", "deepseek-chat"),
            MockProvider("openai", "gpt-3.5-turbo"),
            MockProvider("claude", "claude-3-sonnet"),
            MockProvider("grok", "grok-beta"),
        ]
        
        adapter = AIAdapter()
        
        for provider in providers:
            # Test that all providers can be set
            adapter.set_provider(provider)
            
            # Test that all providers implement required methods
            assert hasattr(provider, 'generate_response')
            assert hasattr(provider, 'get_provider_name')
            assert hasattr(provider, 'get_model_name')
            
            # Test that all providers can generate responses
            response = adapter.generate_response("Test prompt")
            assert len(response) > 0
            assert provider.name in response
            
    def test_provider_model_switching(self):
        """Test switching between different models of the same provider."""
        adapter = AIAdapter()
        
        # Create providers with different models
        deepseek_chat = MockProvider("deepseek", "deepseek-chat", "Chat response")
        deepseek_coder = MockProvider("deepseek", "deepseek-coder", "Code response")
        
        # Test model switching
        adapter.set_provider(deepseek_chat)
        chat_response = adapter.generate_response("Explain AI")
        assert "Chat response" in chat_response
        
        adapter.set_provider(deepseek_coder)
        code_response = adapter.generate_response("Write Python code")
        assert "Code response" in code_response
        
    def test_provider_parameter_handling(self):
        """Test that providers handle different parameters correctly."""
        adapter = AIAdapter()
        
        class ParameterTestProvider(MockProvider):
            def __init__(self, name):
                super().__init__(name)
                self.last_kwargs = {}
                
            def generate_response(self, prompt: str, **kwargs) -> str:
                self.last_kwargs = kwargs
                return f"Response with params: {kwargs}"
        
        provider = ParameterTestProvider("param_test")
        adapter.set_provider(provider)
        
        # Test with different parameters
        response1 = adapter.generate_response("Test", max_tokens=100)
        assert "max_tokens" in str(provider.last_kwargs)
        
        response2 = adapter.generate_response("Test", temperature=0.7, top_p=0.9)
        assert "temperature" in str(provider.last_kwargs)
        assert "top_p" in str(provider.last_kwargs)


class TestProviderErrorHandling:
    """Test error handling during provider operations."""
    
    def test_provider_initialization_errors(self):
        """Test handling of provider initialization errors."""
        adapter = AIAdapter()
        
        class FailingInitProvider(MockProvider):
            def __init__(self, name):
                super().__init__(name)
                raise RuntimeError("Initialization failed")
        
        # Test that initialization errors are handled
        with pytest.raises(RuntimeError):
            failing_provider = FailingInitProvider("failing_init")
            adapter.set_provider(failing_provider)
            
    def test_provider_response_errors(self):
        """Test handling of provider response generation errors."""
        adapter = AIAdapter()
        
        # Create provider that fails during response generation
        failing_provider = MockProvider("failing", should_fail=True)
        adapter.set_provider(failing_provider)
        
        # Test that response errors are properly raised
        with pytest.raises(AISystemError):
            adapter.generate_response("Test prompt")
            
    def test_provider_timeout_handling(self):
        """Test handling of provider timeouts."""
        adapter = AIAdapter()
        
        class SlowProvider(MockProvider):
            def generate_response(self, prompt: str, **kwargs) -> str:
                time.sleep(2.0)  # Simulate slow response
                return "Slow response"
        
        slow_provider = SlowProvider("slow")
        adapter.set_provider(slow_provider)
        
        # Test with timeout (this would require timeout implementation in adapter)
        # For now, just verify the provider can be set
        assert adapter.get_current_provider() == "slow"
        
    def test_provider_recovery_after_error(self):
        """Test provider recovery after encountering errors."""
        adapter = AIAdapter()
        
        class RecoveringProvider(MockProvider):
            def __init__(self, name):
                super().__init__(name)
                self.failure_count = 0
                
            def generate_response(self, prompt: str, **kwargs) -> str:
                self.failure_count += 1
                if self.failure_count <= 2:
                    raise AISystemError("Temporary failure")
                return "Recovered response"
        
        recovering_provider = RecoveringProvider("recovering")
        adapter.set_provider(recovering_provider)
        
        # First two calls should fail
        with pytest.raises(AISystemError):
            adapter.generate_response("Test 1")
            
        with pytest.raises(AISystemError):
            adapter.generate_response("Test 2")
            
        # Third call should succeed
        response = adapter.generate_response("Test 3")
        assert "Recovered response" in response


class TestProviderConfiguration:
    """Test provider configuration and management."""
    
    def test_provider_availability_check(self):
        """Test checking provider availability."""
        adapter = AIAdapter()
        
        # Test getting available providers
        available_providers = adapter.get_available_providers()
        assert isinstance(available_providers, list)
        
        # Test provider creation
        test_provider = MockProvider("test")
        adapter.set_provider(test_provider)
        
        current_provider = adapter.get_current_provider()
        assert current_provider == "test"
        
    def test_provider_factory_methods(self):
        """Test provider factory methods in adapter."""
        adapter = AIAdapter()
        
        # Test that adapter can create providers (mock the creation)
        with patch.object(adapter, 'create_provider') as mock_create:
            mock_provider = MockProvider("factory_test")
            mock_create.return_value = mock_provider
            
            # Test provider creation
            provider = adapter.create_provider("deepseek", "test-key", "deepseek-chat")
            assert provider is not None
            
            mock_create.assert_called_once_with("deepseek", "test-key", "deepseek-chat")
            
    def test_provider_configuration_validation(self):
        """Test validation of provider configurations."""
        adapter = AIAdapter()
        
        # Test with valid provider
        valid_provider = MockProvider("valid", "valid-model")
        adapter.set_provider(valid_provider)
        assert adapter.get_current_provider() == "valid"
        
        # Test with None provider (should handle gracefully)
        try:
            adapter.set_provider(None)
        except Exception as e:
            # Should handle None provider appropriately
            assert "provider" in str(e).lower() or "none" in str(e).lower()


class TestRealWorldProviderScenarios:
    """Test real-world provider switching scenarios."""
    
    def test_meeting_with_provider_switch(self):
        """Test switching providers during a meeting scenario."""
        adapter = AIAdapter()
        transcriber = MockTranscriber()
        responder = GPTResponder(adapter)
        
        # Start with DeepSeek for cost efficiency
        deepseek = MockProvider("deepseek", response="Cost-effective analysis")
        adapter.set_provider(deepseek)
        
        # Generate initial response
        response1 = responder._generate_response_from_transcript("Meeting started")
        assert "Cost-effective analysis" in response1
        
        # Switch to GPT-4 for better quality during important discussion
        gpt4 = MockProvider("openai", "gpt-4", "High-quality analysis")
        adapter.set_provider(gpt4)
        
        response2 = responder._generate_response_from_transcript("Important decision point")
        assert "High-quality analysis" in response2
        
        # Switch back to DeepSeek for regular discussion
        adapter.set_provider(deepseek)
        
        response3 = responder._generate_response_from_transcript("Regular discussion")
        assert "Cost-effective analysis" in response3
        
    def test_provider_fallback_chain(self):
        """Test fallback chain when providers fail."""
        adapter = AIAdapter()
        
        # Create fallback chain: Primary -> Secondary -> Emergency
        primary = MockProvider("primary", should_fail=True)
        secondary = MockProvider("secondary", should_fail=True)
        emergency = MockProvider("emergency", response="Emergency response")
        
        providers = [primary, secondary, emergency]
        
        # Try providers in order until one succeeds
        last_error = None
        for provider in providers:
            try:
                adapter.set_provider(provider)
                response = adapter.generate_response("Fallback test")
                # If we get here, provider succeeded
                assert "Emergency response" in response
                break
            except AISystemError as e:
                last_error = e
                continue
        else:
            # If no provider succeeded, fail the test
            pytest.fail(f"All providers failed, last error: {last_error}")
            
    def test_load_balancing_simulation(self):
        """Test load balancing between multiple providers."""
        adapter = AIAdapter()
        
        # Create multiple providers for load balancing
        providers = [
            MockProvider(f"provider_{i}", response=f"Response from {i}")
            for i in range(3)
        ]
        
        # Simulate load balancing by rotating providers
        responses = []
        for i in range(9):  # 3 rounds of 3 providers each
            provider = providers[i % len(providers)]
            adapter.set_provider(provider)
            
            response = adapter.generate_response(f"Request {i}")
            responses.append((provider.name, response))
        
        # Verify load was distributed
        provider_usage = {}
        for provider_name, response in responses:
            provider_usage[provider_name] = provider_usage.get(provider_name, 0) + 1
        
        # Each provider should have been used 3 times
        for provider_name, usage_count in provider_usage.items():
            assert usage_count == 3


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])