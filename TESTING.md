# Testing Guide

Comprehensive testing documentation for the CyberSec Teaching Tool.

## Table of Contents

- [Overview](#overview)
- [Frontend Testing](#frontend-testing)
- [Backend Testing](#backend-testing)
- [Common Patterns](#common-patterns)
- [Troubleshooting](#troubleshooting)
- [CI/CD Integration](#cicd-integration)
- [Best Practices](#best-practices)

## Overview

### Testing Strategy

This project uses a comprehensive testing approach:

- **Unit Tests**: Test individual components/functions in isolation
- **Integration Tests**: Test interactions between components/services
- **Accessibility Tests**: Ensure WCAG 2.1 AA compliance
- **API Tests**: Verify backend endpoints and data flow

### Test Coverage Goals

- **Frontend**: 80%+ coverage for components, 90%+ for utilities
- **Backend**: 85%+ coverage for services, 95%+ for API routes

### Quick Commands

```bash
# Frontend
cd frontend
npm test                    # Run all tests in watch mode
npm run test:ui            # Open Vitest UI
npm run test:coverage      # Generate coverage report

# Backend
cd backend
pytest                     # Run all tests
pytest -v                  # Verbose output
pytest --cov=app          # With coverage report
pytest -k "test_name"     # Run specific test
```

## Frontend Testing

### Tech Stack

- **Test Runner**: [Vitest](https://vitest.dev/)
- **Testing Library**: [React Testing Library](https://testing-library.com/react)
- **Environment**: jsdom (browser simulation)
- **Coverage**: v8 (built into Vitest)

### Test Structure

```
frontend/src/
├── components/
│   ├── common/
│   │   ├── Button.tsx
│   │   └── Button.test.tsx
│   └── network/
│       ├── DeviceNode.tsx
│       └── DeviceNode.test.tsx
├── hooks/
│   ├── useDevices.ts
│   └── useDevices.test.ts
└── test/
    ├── setup.ts          # Global test setup
    └── mocks.ts          # Shared mock utilities
```

### Writing Component Tests

#### Basic Component Test

```typescript
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Button } from './Button';

describe('Button', () => {
  it('renders with text', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByRole('button', { name: 'Click me' })).toBeInTheDocument();
  });

  it('handles click events', () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Click me</Button>);

    fireEvent.click(screen.getByRole('button'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});
```

#### Testing with Context

Components that use context providers need to be wrapped:

```typescript
import { ThemeProvider } from '@/context/ThemeContext';

function TestWrapper({ children }: { children: React.ReactNode }) {
  return <ThemeProvider>{children}</ThemeProvider>;
}

it('renders with theme context', () => {
  render(
    <TestWrapper>
      <MyComponent />
    </TestWrapper>
  );
  // assertions...
});
```

#### Testing Async Operations

Use `waitFor` for assertions that depend on async state updates:

```typescript
import { waitFor } from '@testing-library/react';

it('loads data asynchronously', async () => {
  render(<DataComponent />);

  expect(screen.getByText('Loading...')).toBeInTheDocument();

  await waitFor(() => {
    expect(screen.getByText('Data loaded')).toBeInTheDocument();
  });
});
```

### Dialog Element Testing

jsdom doesn't fully support native `<dialog>` elements. Mock the methods in each test:

```typescript
import { beforeEach } from 'vitest';

describe('MyDialog', () => {
  beforeEach(() => {
    // Mock dialog methods
    HTMLDialogElement.prototype.showModal = vi.fn(function (this: HTMLDialogElement) {
      this.setAttribute('open', '');
    });
    HTMLDialogElement.prototype.close = vi.fn(function (this: HTMLDialogElement) {
      this.removeAttribute('open');
    });
  });

  it('opens dialog', () => {
    render(<MyDialog isOpen={true} />);
    expect(screen.getByRole('dialog')).toBeInTheDocument();
  });
});
```

### CSS Modules Testing

CSS modules hash class names for scoping. Use regex matching:

```typescript
// ❌ Don't do this
expect(element).toHaveClass('selected');

// ✅ Do this
expect(element.className).toMatch(/selected/);
```

### Testing Custom Hooks

```typescript
import { renderHook, waitFor } from '@testing-library/react';
import { useDevices } from './useDevices';

describe('useDevices', () => {
  it('fetches devices on mount', async () => {
    const { result } = renderHook(() => useDevices('scan-1'));

    expect(result.current.loading).toBe(true);

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
      expect(result.current.data).toHaveLength(3);
    });
  });
});
```

### Mocking API Calls

Use the `mockFetch` utility from `@/test/mocks`:

```typescript
import { mockFetch } from '@/test/mocks';

beforeEach(() => {
  mockFetch({
    '/api/devices': { status: 200, data: mockDevices }
  });
});
```

### Accessibility Testing

Every component should test accessibility:

```typescript
describe('Button accessibility', () => {
  it('has accessible label', () => {
    render(<Button aria-label="Submit form">Submit</Button>);
    expect(screen.getByLabelText('Submit form')).toBeInTheDocument();
  });

  it('supports keyboard navigation', () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Click</Button>);

    const button = screen.getByRole('button');
    button.focus();
    fireEvent.keyDown(button, { key: 'Enter' });

    expect(handleClick).toHaveBeenCalled();
  });

  it('has minimum touch target size', () => {
    render(<Button>Click</Button>);
    const button = screen.getByRole('button');
    const styles = window.getComputedStyle(button);

    // WCAG 2.1 AA requires 44x44px minimum
    expect(parseInt(styles.minHeight)).toBeGreaterThanOrEqual(44);
    expect(parseInt(styles.minWidth)).toBeGreaterThanOrEqual(44);
  });
});
```

### Logger Testing

Components using the logger must create an instance:

```typescript
// ❌ Wrong
import { logger } from '@/services/logger';
logger.debug('message');  // TypeError: logger.debug is not a function

// ✅ Correct
import { logger } from '@/services/logger';
const log = logger.create('ComponentName');
log.debug('message');  // Works correctly
```

## Backend Testing

### Tech Stack

- **Test Runner**: [pytest](https://pytest.org/)
- **HTTP Client**: FastAPI TestClient
- **Fixtures**: conftest.py for shared test data
- **Coverage**: pytest-cov

### Test Structure

```
backend/tests/
├── conftest.py           # Shared fixtures
├── api/
│   ├── test_devices.py
│   └── test_scans.py
├── services/
│   ├── scanner/
│   │   └── test_scanner.py
│   └── datastore/
│       └── test_local_datastore.py
└── models/
    └── test_device.py
```

### Writing API Tests

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_list_devices():
    """Test GET /api/devices endpoint."""
    response = client.get("/api/devices")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_create_scan():
    """Test POST /api/scans endpoint."""
    response = client.post(
        "/api/scans",
        json={
            "network": "192.168.1.0/24",
            "scan_type": "quick"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["network"] == "192.168.1.0/24"
```

### Using Fixtures

Define reusable fixtures in `conftest.py`:

```python
# backend/tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)

@pytest.fixture
def sample_device():
    """Sample device data."""
    return {
        "ip": "192.168.1.1",
        "mac": "00:1A:2B:3C:4D:5E",
        "hostname": "router.local",
        "device_type": "router"
    }

@pytest.fixture
def mock_nmap(monkeypatch):
    """Mock nmap scanner."""
    def mock_scan(*args, **kwargs):
        return {"192.168.1.1": {"state": "up"}}

    monkeypatch.setattr("nmap.PortScanner.scan", mock_scan)
```

Use fixtures in tests:

```python
def test_with_fixtures(client, sample_device):
    """Test using fixtures."""
    response = client.post("/api/devices", json=sample_device)
    assert response.status_code == 201
```

### Testing DataStore

The DataStore abstraction is critical for multi-user support:

```python
from app.services.datastore.local import LocalDataStore

def test_datastore_add_device():
    """Test adding device to datastore."""
    store = LocalDataStore()
    device = store.add_device(
        scan_id="scan-1",
        ip="192.168.1.1",
        device_type="router"
    )
    assert device.id is not None
    assert device.ip == "192.168.1.1"

def test_datastore_list_devices():
    """Test listing devices from datastore."""
    store = LocalDataStore()
    devices = store.list_devices(scan_id="scan-1")
    assert isinstance(devices, list)
```

### Testing Async Functions

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    """Test async function."""
    result = await my_async_function()
    assert result is not None
```

### Mocking External Services

Mock nmap for scanner tests:

```python
def test_scan_network(mock_nmap):
    """Test network scanning with mocked nmap."""
    from app.services.scanner import NetworkScanner

    scanner = NetworkScanner()
    results = scanner.scan("192.168.1.0/24")

    assert len(results) > 0
    assert "192.168.1.1" in results
```

## Common Patterns

### Test Organization

```typescript
describe('ComponentName', () => {
  // Setup
  const defaultProps = {
    prop1: 'value1',
    prop2: vi.fn()
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  // Rendering tests
  describe('rendering', () => {
    it('renders with required props', () => {
      // test
    });
  });

  // Interaction tests
  describe('interactions', () => {
    it('handles click events', () => {
      // test
    });
  });

  // Accessibility tests
  describe('accessibility', () => {
    it('has proper ARIA labels', () => {
      // test
    });
  });
});
```

### Testing Error States

```typescript
it('displays error message when fetch fails', async () => {
  mockFetch({
    '/api/devices': { status: 500, error: 'Server error' }
  });

  render(<DeviceList />);

  await waitFor(() => {
    expect(screen.getByText(/error/i)).toBeInTheDocument();
  });
});
```

### Testing Loading States

```typescript
it('shows loading indicator while fetching', () => {
  render(<DeviceList />);
  expect(screen.getByText('Loading...')).toBeInTheDocument();
});

it('hides loading indicator after data loads', async () => {
  render(<DeviceList />);

  await waitFor(() => {
    expect(screen.queryByText('Loading...')).not.toBeInTheDocument();
  });
});
```

## Troubleshooting

### Common Issues

#### Issue: `TypeError: logger.debug is not a function`

**Cause**: Calling logger methods directly instead of creating an instance.

**Fix**:
```typescript
// Wrong
import { logger } from '@/services/logger';
logger.debug('message');

// Correct
import { logger } from '@/services/logger';
const log = logger.create('ModuleName');
log.debug('message');
```

#### Issue: `Unable to find an accessible element with the role "dialog"`

**Cause**: jsdom doesn't support native `<dialog>` element properly.

**Fix**: Mock the dialog methods in your test:
```typescript
beforeEach(() => {
  HTMLDialogElement.prototype.showModal = vi.fn(function (this: HTMLDialogElement) {
    this.setAttribute('open', '');
  });
  HTMLDialogElement.prototype.close = vi.fn(function (this: HTMLDialogElement) {
    this.removeAttribute('open');
  });
});
```

#### Issue: `Expected element to have class "selected"`

**Cause**: CSS modules hash class names.

**Fix**: Use regex matching:
```typescript
expect(element.className).toMatch(/selected/);
```

#### Issue: `Warning: An update to Component inside a test was not wrapped in act(...)`

**Cause**: Async state updates not wrapped properly.

**Fix**: Use `waitFor`:
```typescript
await waitFor(() => {
  expect(element).toHaveTextContent('Updated');
});
```

#### Issue: `Found multiple elements with the role "button" and name /close/i`

**Cause**: Multiple buttons match the same query.

**Fix**: Use more specific selectors:
```typescript
// Use exact match
screen.getByRole('button', { name: /^Close$/i })

// Or use getAllByRole and select by index
const buttons = screen.getAllByRole('button', { name: /close/i });
fireEvent.click(buttons[1]);
```

### WSL/Linux Testing Issues

#### Issue: npm uses Windows Node.js in WSL

**Cause**: Windows Node.js in PATH takes precedence over Linux version.

**Fix**: Install Node.js natively in WSL using nvm:
```bash
# Install nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash

# Load nvm
source ~/.bashrc

# Install Node.js LTS
nvm install --lts

# Verify
which node  # Should show /home/user/.nvm/...
which npm   # Should show /home/user/.nvm/...
```

## CI/CD Integration

### GitHub Actions

Example workflow for running tests:

```yaml
name: Test

on: [push, pull_request]

jobs:
  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '20'
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
      - name: Run tests
        run: |
          cd frontend
          npm test -- --run
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./frontend/coverage/coverage-final.json

  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements-dev.txt
      - name: Run tests
        run: |
          cd backend
          pytest --cov=app --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./backend/coverage.xml
```

## Best Practices

### General

1. **Test behavior, not implementation**: Focus on what the component does, not how it does it
2. **Write descriptive test names**: Use "should" or "it" format
3. **One assertion per test**: Keep tests focused and easy to debug
4. **Use data-testid sparingly**: Prefer semantic queries (role, label, text)
5. **Clean up after tests**: Clear mocks, reset state in `beforeEach`

### Frontend

1. **Query priority** (React Testing Library):
   - `getByRole` (best for accessibility)
   - `getByLabelText`
   - `getByText`
   - `getByTestId` (last resort)

2. **Avoid testing library internals**: Don't test state or props directly

3. **Test user interactions**: Click, type, submit forms like a user would

4. **Mock at the right level**: Mock at the API boundary, not internal functions

### Backend

1. **Use fixtures for common data**: Define in `conftest.py`

2. **Test database operations**: Ensure data integrity and relationships

3. **Test error cases**: Verify proper error handling and status codes

4. **Isolate tests**: Each test should be independent

5. **Use meaningful test data**: Makes debugging easier

### Accessibility

1. **Test keyboard navigation**: All interactive elements should be keyboard accessible

2. **Test ARIA attributes**: Verify proper labels, roles, and states

3. **Test focus management**: Ensure focus moves logically

4. **Test color independence**: Information should not rely solely on color

5. **Test screen reader announcements**: Use `aria-live` regions appropriately

### Performance

1. **Keep tests fast**: Mock slow operations (network, file I/O)

2. **Run tests in parallel**: Use Vitest's default parallel mode

3. **Use watch mode in development**: Faster feedback loop

4. **Generate coverage periodically**: Not on every test run

## Coverage Reports

### Frontend

Generate coverage report:
```bash
cd frontend
npm run test:coverage
```

View HTML report:
```bash
open coverage/index.html
```

### Backend

Generate coverage report:
```bash
cd backend
pytest --cov=app --cov-report=html
```

View HTML report:
```bash
open htmlcov/index.html
```

## Resources

### Frontend
- [Vitest Documentation](https://vitest.dev/)
- [React Testing Library](https://testing-library.com/react)
- [Testing Library Queries](https://testing-library.com/docs/queries/about)
- [Common Testing Mistakes](https://kentcdodds.com/blog/common-mistakes-with-react-testing-library)

### Backend
- [pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [pytest Fixtures](https://docs.pytest.org/en/stable/fixture.html)

### Accessibility
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/)
- [Testing Library Accessibility](https://testing-library.com/docs/queries/byrole/)
