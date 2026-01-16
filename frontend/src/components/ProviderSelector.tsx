/**
 * ProviderSelector component
 * Allows users to select AI provider and model
 * Requirements: 1.6
 */

import { Box, FormControl, InputLabel, Select, MenuItem, Typography, type SelectChangeEvent } from '@mui/material';

interface ProviderSelectorProps {
  currentProvider: string;
  currentModel: string;
  availableProviders: string[];
  availableModels: Record<string, string[]>;
  onProviderChange: (provider: string) => void;
  onModelChange: (model: string) => void;
}

export function ProviderSelector({
  currentProvider,
  currentModel,
  availableProviders,
  availableModels,
  onProviderChange,
  onModelChange,
}: ProviderSelectorProps) {
  const handleProviderChange = (event: SelectChangeEvent) => {
    const newProvider = event.target.value;
    onProviderChange(newProvider);
    
    // Auto-select first model for the new provider
    const models = availableModels[newProvider];
    if (models && models.length > 0) {
      onModelChange(models[0]);
    }
  };

  const handleModelChange = (event: SelectChangeEvent) => {
    onModelChange(event.target.value);
  };

  const currentProviderModels = availableModels[currentProvider] || [];

  return (
    <Box>
      {/* Provider Selection */}
      <FormControl fullWidth sx={{ mb: 2 }}>
        <InputLabel id="provider-select-label">AI Provider</InputLabel>
        <Select
          labelId="provider-select-label"
          id="provider-select"
          value={currentProvider}
          label="AI Provider"
          onChange={handleProviderChange}
        >
          {availableProviders.map((provider) => (
            <MenuItem key={provider} value={provider}>
              {provider}
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      {/* Model Selection */}
      <FormControl fullWidth>
        <InputLabel id="model-select-label">Model</InputLabel>
        <Select
          labelId="model-select-label"
          id="model-select"
          value={currentModel}
          label="Model"
          onChange={handleModelChange}
          disabled={currentProviderModels.length === 0}
        >
          {currentProviderModels.map((model) => (
            <MenuItem key={model} value={model}>
              {model}
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
        Current: {currentProvider} - {currentModel}
      </Typography>
    </Box>
  );
}
