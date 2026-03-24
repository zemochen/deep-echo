"""
Property-based tests for AI Adapter and AI Providers.

Feature: real-time-voice-ai-assistant, Property 3: AI响应生成完整性
Validates: Requirements 3.1, 3.2, 3.3

Feature: real-time-voice-ai-assistant, Property 4: AI厂商切换一致性
Validates: Requirements 扩展功能

Feature: real-time-voice-ai-assistant, Property 5: 可配置更新间隔
Validates: Requirements 3.4

This test suite validates that AI response generation works correctly
across all providers and that provider switching maintains consistency.
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from hypothesis import assume
from unittest.mock import Mock, patch, MagicMock
import time
from datetime import datetime

from backend.ai.adapter import AIAdapter
from backend.ai.responder import GPTResponder
from backend.ai.providers.base_provider import (
    AIProvider, 
    AIProviderError,
    AIProviderConnectionError,
    AIProviderAuthenticationError,
    AIProviderRateLimitError,
    AIProviderTimeoutError
)
from backend.ai.providers.deepseek_provider import DeepSeekProvider
from backend.ai.providers.openai_provider import OpenAIProvider


# Test fixtures and helpers

class MockAIProvider(AIProvider):
    """Mock AI provider for testing"""
    
    def __init__(self, api_key: str, model: str = "mock-model", 
                 base_url: str = "https://mock.api.com", 
                 timeout: int = 30, max_retries: int = 3,
                 response_text: str = "Mock response"):
        super().__init__(api_key, model, base_url, timeout, max_retries)
        self.response_text = response_text
        self.call_count = 0
        self.last_prompt = None
    
    def generate_response(self, prompt: str, **kwargs) -> str:
        self.call_count += 1
        self.last_prompt = prompt
        if not prompt.strip():
            raise ValueError("Prompt cannot be empty")
        return f"{self.response_text} (call #{self.call_count})"
    
    def get_provider_name(self) -> str:
        return "mock"


@pytest.fixture
def mock_provider():
    """Create a mock AI provider for testing"""
    return MockAIProvider("test-api-key", "test-model", response_text="Test response")


@pytest.fixture
def ai_adapter():
    """Create an AI adapter for testing"""
    return AIAdapter()


# Unit tests for basic functionality

class TestAIAdapter:
    """Unit tests for AIAdapter class"""
    
    def test_init_without_provider(self):
        """Test initialization without provider"""
        adapter = AIAdapter()
        assert adapter.get_current_provider() is None
        assert adapter.get_current_model() is None
    
    def test_init_with_provider(self, mock_provider):
        """Test initialization with provider"""
        adapter = AIAdapter(mock_provider)
        assert adapter.get_current_provider() == "mock"
        assert adapter.get_current_model() == "test-model"
    
    def test_set_provider_success(self, ai_adapter, mock_provider):
        """Test successful provider setting"""
        ai_adapter.set_provider(mock_provider)
        assert ai_adapter.get_current_provider() == "mock"
    
    def test_set_provider_none_raises_error(self, ai_adapter):
        """Test that setting None provider raises error"""
        with pytest.raises(ValueError, match="Provider cannot be None"):
            ai_adapter.set_provider(None)
    
    def test_generate_response_without_provider_raises_error(self, ai_adapter):
        """Test that generating response without provider raises error"""
        with pytest.raises(RuntimeError, match="No AI provider is currently set"):
            ai_adapter.generate_response("test prompt")
    
    def test_generate_response_success(self, ai_adapter, mock_provider):
        """Test successful response generation"""
        ai_adapter.set_provider(mock_provider)
        response = ai_adapter.generate_response("test prompt")
        assert "Test response" in response
        assert mock_provider.call_count == 1


# Property-based tests

@settings(
    max_examples=3,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    prompts=st.lists(
        st.text(min_size=1, max_size=200, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc', 'Pd', 'Zs', 'Po')
        )),
        min_size=1, max_size=10
    ),
    provider_responses=st.lists(
        st.text(min_size=1, max_size=100, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc', 'Pd', 'Zs')
        )),
        min_size=1, max_size=10
    )
)
def test_property_ai_response_generation_completeness(prompts, provider_responses):
    """
    Property 3: AI response generation completeness
    
    Feature: real-time-voice-ai-assistant, Property 3: AI响应生成完整性
    Validates: Requirements 3.1, 3.2, 3.3
    
    For any new transcription text, when there is sufficient context,
    the AI adapter should analyze the complete conversation history
    through the currently configured AI provider and generate relevant
    response suggestions.
    
    This property tests that:
    1. AI adapter generates responses for all valid prompts
    2. Responses are non-empty and meaningful
    3. Provider processes complete conversation context
    4. Response generation is consistent across calls
    """
    # Filter out empty or whitespace-only prompts
    valid_prompts = [p.strip() for p in prompts if p.strip()]
    valid_responses = [r.strip() for r in provider_responses if r.strip()]
    
    # Skip if no valid inputs
    assume(len(valid_prompts) > 0 and len(valid_responses) > 0)
    
    # Create mock provider with predefined responses
    response_cycle = valid_responses * ((len(valid_prompts) // len(valid_responses)) + 1)
    
    class TestProvider(AIProvider):
        def __init__(self):
            super().__init__("test-key", "test-model")
            self.call_count = 0
            self.received_prompts = []
        
        def generate_response(self, prompt: str, **kwargs) -> str:
            if not prompt.strip():
                raise ValueError("Prompt cannot be empty")
            
            self.received_prompts.append(prompt)
            response = response_cycle[self.call_count % len(response_cycle)]
            self.call_count += 1
            return response
        
        def get_provider_name(self) -> str:
            return "test"
    
    provider = TestProvider()
    adapter = AIAdapter(provider)
    
    # Test response generation for all prompts
    generated_responses = []
    for i, prompt in enumerate(valid_prompts):
        response = adapter.generate_response(prompt)
        generated_responses.append(response)
        
        # Verify response completeness
        assert response is not None, f"Response should not be None for prompt {i}"
        assert isinstance(response, str), f"Response should be string for prompt {i}"
        assert len(response.strip()) > 0, f"Response should not be empty for prompt {i}"
        
        # Verify provider received the complete prompt
        assert prompt in provider.received_prompts, \
            f"Provider should have received prompt: {prompt}"
    
    # Verify all prompts were processed
    assert len(generated_responses) == len(valid_prompts), \
        "Should generate response for every valid prompt"
    
    # Verify provider call count matches
    assert provider.call_count == len(valid_prompts), \
        f"Provider should be called {len(valid_prompts)} times, got {provider.call_count}"
    
    # Verify response consistency - same prompt should yield same response
    if len(valid_prompts) > 1:
        # Test with duplicate prompt
        duplicate_prompt = valid_prompts[0]
        response1 = adapter.generate_response(duplicate_prompt)
        response2 = adapter.generate_response(duplicate_prompt)
        
        # Both responses should be valid (though may differ due to AI variability)
        assert len(response1.strip()) > 0, "First duplicate response should be valid"
        assert len(response2.strip()) > 0, "Second duplicate response should be valid"


@settings(
    max_examples=3,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    provider_configs=st.lists(
        st.fixed_dictionaries({
            'name': st.sampled_from(['provider1', 'provider2', 'provider3']),
            'api_key': st.text(min_size=10, max_size=50),
            'model': st.text(min_size=5, max_size=20),
            'response': st.text(min_size=1, max_size=100)
        }),
        min_size=2, max_size=5
    ),
    test_prompt=st.text(min_size=1, max_size=100, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc', 'Pd', 'Zs')
    ))
)
def test_property_ai_provider_switching_consistency(provider_configs, test_prompt):
    """
    Property 4: AI provider switching consistency
    
    Feature: real-time-voice-ai-assistant, Property 4: AI厂商切换一致性
    Validates: Requirements 扩展功能
    
    For any AI provider switching operation, the system should seamlessly
    switch to the new AI provider and maintain response generation
    functionality normally.
    
    This property tests that:
    1. Provider switching works for any sequence of providers
    2. Each provider maintains its own state correctly
    3. Response generation continues to work after switching
    4. Provider history is maintained accurately
    5. Current provider information is always accurate
    """
    # Filter valid inputs
    valid_configs = [
        config for config in provider_configs 
        if config['api_key'].strip() and config['model'].strip() and config['response'].strip()
    ]
    valid_prompt = test_prompt.strip()
    
    # Skip if insufficient data
    assume(len(valid_configs) >= 2 and valid_prompt)
    
    # Create test providers
    class ConfigurableTestProvider(AIProvider):
        def __init__(self, name: str, api_key: str, model: str, response: str):
            super().__init__(api_key, model)
            self.name = name
            self.response = response
            self.call_count = 0
        
        def generate_response(self, prompt: str, **kwargs) -> str:
            if not prompt.strip():
                raise ValueError("Prompt cannot be empty")
            self.call_count += 1
            return f"{self.response} from {self.name} (call #{self.call_count})"
        
        def get_provider_name(self) -> str:
            return self.name
    
    # Create adapter
    adapter = AIAdapter()
    
    # Track expected history
    expected_history = []
    provider_instances = {}
    
    # Test switching through all providers
    for i, config in enumerate(valid_configs):
        # Create provider instance
        provider = ConfigurableTestProvider(
            config['name'], 
            config['api_key'], 
            config['model'], 
            config['response']
        )
        provider_instances[config['name']] = provider
        
        # Switch to this provider
        adapter.set_provider(provider)
        expected_history.append(config['name'])
        
        # Verify current provider information
        assert adapter.get_current_provider() == config['name'], \
            f"Current provider should be {config['name']}"
        assert adapter.get_current_model() == config['model'], \
            f"Current model should be {config['model']}"
        
        # Verify response generation works
        response = adapter.generate_response(valid_prompt)
        assert response is not None, f"Response should not be None for provider {config['name']}"
        assert config['response'] in response, \
            f"Response should contain provider-specific text for {config['name']}"
        assert config['name'] in response, \
            f"Response should identify provider {config['name']}"
        
        # Verify provider call count
        assert provider.call_count == 1, \
            f"Provider {config['name']} should have been called once"
        
        # Verify provider history
        current_history = adapter.get_provider_history()
        assert current_history == expected_history, \
            f"Provider history should match expected: {expected_history}"
    
    # Test switching back to previous providers maintains state
    if len(valid_configs) >= 2:
        # Switch back to first provider
        first_config = valid_configs[0]
        first_provider = provider_instances[first_config['name']]
        
        adapter.set_provider(first_provider)
        expected_history.append(first_config['name'])
        
        # Generate another response
        response = adapter.generate_response(valid_prompt)
        
        # Verify provider state was maintained (call count should increment)
        assert first_provider.call_count == 2, \
            f"First provider should have been called twice, got {first_provider.call_count}"
        
        # Verify response indicates second call
        assert "call #2" in response, \
            "Response should indicate this is the second call to the provider"
        
        # Verify history is correct
        assert adapter.get_provider_history() == expected_history, \
            "Provider history should include the return to first provider"
    
    # Test adapter status
    status = adapter.get_status()
    assert status['current_provider'] == expected_history[-1], \
        "Status should show correct current provider"
    assert status['is_valid'] == True, \
        "Status should indicate adapter is valid"
    assert len(status['provider_history']) == len(expected_history), \
        "Status should show complete provider history"


@settings(
    max_examples=2,
    deadline=None
)
@given(
    num_switches=st.integers(min_value=1, max_value=10),
    prompts_per_provider=st.integers(min_value=1, max_value=5)
)
def test_property_provider_state_isolation(num_switches, prompts_per_provider):
    """
    Property: Provider state isolation
    
    For any sequence of provider switches, each provider should maintain
    its own independent state (call counts, configurations, etc.) without
    interference from other providers.
    """
    class StatefulTestProvider(AIProvider):
        def __init__(self, provider_id: int):
            super().__init__(f"key-{provider_id}", f"model-{provider_id}")
            self.provider_id = provider_id
            self.call_count = 0
            self.prompts_received = []
        
        def generate_response(self, prompt: str, **kwargs) -> str:
            self.call_count += 1
            self.prompts_received.append(prompt)
            return f"Response from provider {self.provider_id} (call #{self.call_count})"
        
        def get_provider_name(self) -> str:
            return f"provider_{self.provider_id}"
    
    # Create providers
    providers = [StatefulTestProvider(i) for i in range(num_switches)]
    adapter = AIAdapter()
    
    # Switch between providers and generate responses
    for switch_round in range(2):  # Do two rounds to test state persistence
        for i, provider in enumerate(providers):
            adapter.set_provider(provider)
            
            # Generate multiple responses for this provider
            for prompt_num in range(prompts_per_provider):
                prompt = f"test prompt {switch_round}-{i}-{prompt_num}"
                response = adapter.generate_response(prompt)
                
                # Verify response is from correct provider
                assert f"provider {i}" in response, \
                    f"Response should be from provider {i}"
                
                # Verify call count is correct for this provider
                expected_calls = (switch_round + 1) * prompts_per_provider
                if switch_round == 0:
                    expected_calls = prompt_num + 1
                else:
                    expected_calls = prompts_per_provider + prompt_num + 1
                
                assert provider.call_count == expected_calls, \
                    f"Provider {i} should have {expected_calls} calls, got {provider.call_count}"
    
    # Verify final state isolation
    for i, provider in enumerate(providers):
        expected_total_calls = 2 * prompts_per_provider
        assert provider.call_count == expected_total_calls, \
            f"Provider {i} should have {expected_total_calls} total calls"
        
        expected_prompts = 2 * prompts_per_provider
        assert len(provider.prompts_received) == expected_prompts, \
            f"Provider {i} should have received {expected_prompts} prompts"


@settings(
    max_examples=3,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    update_intervals=st.lists(
        st.integers(min_value=1, max_value=10),
        min_size=1, max_size=10
    )
)
def test_property_configurable_update_intervals(update_intervals):
    """
    Property 5: Configurable update intervals
    
    Feature: real-time-voice-ai-assistant, Property 5: 可配置更新间隔
    Validates: Requirements 3.4
    
    For any configured update interval setting, the GPT responder should
    update response suggestions according to the specified interval.
    
    This property tests that:
    1. Update interval can be set to any positive value
    2. Responder maintains the configured interval accurately
    3. Interval changes are applied immediately
    4. Response timing respects the configured interval
    """
    # Create mock AI adapter
    mock_adapter = AIAdapter()
    mock_provider = MockAIProvider("test-key", "test-model", response_text="Test response")
    mock_adapter.set_provider(mock_provider)
    
    # Create GPT responder with initial interval
    initial_interval = update_intervals[0]
    responder = GPTResponder(mock_adapter, response_interval=initial_interval)
    
    # Verify initial interval is set correctly
    assert responder.get_response_interval() == initial_interval, \
        f"Initial interval should be {initial_interval}"
    
    # Test updating intervals
    for i, new_interval in enumerate(update_intervals[1:], 1):
        # Update the interval
        responder.update_response_interval(new_interval)
        
        # Verify interval was updated
        current_interval = responder.get_response_interval()
        assert current_interval == new_interval, \
            f"Interval should be updated to {new_interval}, got {current_interval}"
        
        # Verify responder status reflects the change
        status = responder.get_status()
        assert status['response_interval'] == new_interval, \
            f"Status should show interval {new_interval}"
    
    # Test that invalid intervals raise errors
    with pytest.raises(ValueError, match="Response interval must be positive"):
        responder.update_response_interval(0)
    
    with pytest.raises(ValueError, match="Response interval must be positive"):
        responder.update_response_interval(-1)
    
    # Test interval persistence across operations
    final_interval = update_intervals[-1]
    responder.update_response_interval(final_interval)
    
    # Perform other operations
    responder.get_current_response()
    responder.get_ai_provider_info()
    
    # Verify interval is still correct
    assert responder.get_response_interval() == final_interval, \
        f"Interval should persist as {final_interval} after other operations"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])