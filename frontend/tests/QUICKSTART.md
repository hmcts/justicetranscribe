# Quick Start Guide - Frontend Testing

## 🚀 Quick Commands

```bash
# Run all tests (unit tests only by default)
npm test

# Run unit tests
npm run test:unit

# Run integration tests (requires backend running)
npm run test:integration

# Watch mode for development
npm run test:watch

# Generate coverage report
npm run test:coverage

# Run integration tests with helper script
./tests/run-integration.sh
```

## 📋 Prerequisites for Integration Tests

1. **Start the backend server:**
   ```bash
   cd backend
   make backend
   ```

2. **Verify backend is running:**
   ```bash
   curl http://localhost:8000/health
   ```

3. **Set environment variables (or use run-integration.sh):**
   ```bash
   export TEST_INTEGRATION=true
   export NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

## 🎯 What Gets Tested

### Unit Tests (`tests/unit/`)
✅ Azure Block Blob API usage  
✅ Chunked upload logic  
✅ Progress reporting  
✅ Error handling  
✅ File extension handling  
✅ SAS token parsing  

**No network calls** - Everything is mocked

### Integration Tests (`tests/integration/`)
✅ Real uploads to justicetransdevstor  
✅ Single PUT request (small files)  
✅ Chunked upload (large files)  
✅ Pre-existing chunk upload  
✅ Performance measurements  
✅ Automatic cleanup  

**Real network calls** - Tests actual Azure integration

## 📊 Expected Test Output

### Unit Tests (Fast - ~100ms)
```
✓ tests/unit/azure-upload.unit.test.ts (27 tests)
  Azure Upload Unit Tests
    uploadBlobAsChunks - Single Blob
      ✓ should split blob into 1MB chunks
      ✓ should handle small blobs
      ✓ should report progress correctly
      ...
```

### Integration Tests (Slower - ~30s)
```
✓ tests/integration/azure-upload.integration.test.ts (8 tests)
  Azure Upload Integration Tests
    ✓ should successfully upload a small blob (3456ms)
    ✓ should successfully upload a large blob (12345ms)
    ...
  
🧹 Cleaning up 8 test blobs...
  - Would delete: user-uploads/test@example.com/abc123.mp4
```

## 🐛 Troubleshooting

### "Backend is NOT running"
```bash
cd backend
source .venv/bin/activate
make backend
```

### "TEST_INTEGRATION is not true"
Use the helper script:
```bash
./tests/run-integration.sh
```

Or set the variable:
```bash
export TEST_INTEGRATION=true
npm run test:integration
```

### Tests hanging or timing out
- Check backend logs for errors
- Increase timeout in test (default: 30s)
- Verify network connectivity to Azure

### Module resolution errors
```bash
# Rebuild node_modules
npm ci
```

## 📁 File Structure

```
tests/
├── unit/                                  # Fast, mocked tests
│   └── azure-upload.unit.test.ts         # Upload logic tests
├── integration/                           # Slow, real service tests  
│   └── azure-upload.integration.test.ts  # Azure upload tests
├── fixtures.ts                            # Mock data generators
├── setup.ts                               # Vitest configuration
├── run-integration.sh                     # Helper script
├── QUICKSTART.md                          # This file
└── README.md                              # Detailed documentation
```

## 💡 Tips

1. **Run unit tests during development** - They're fast and catch logic errors
2. **Run integration tests before pushing** - Verify Azure integration
3. **Use watch mode for TDD** - `npm run test:watch`
4. **Check coverage regularly** - `npm run test:coverage`
5. **Read backend logs** - Integration tests show up in backend logs

## 🔗 Related Files

- **Source code:** `lib/azure-upload.ts`
- **Backend integration tests:** `backend/tests/integration/app/audio/test_azure_blob_integration.py`
- **Vitest config:** `vitest.config.ts`

