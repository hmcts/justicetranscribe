# What's New Modal Component

## Overview

The `WhatsNewModal` is an Apple-inspired notification modal that displays important announcements about new features and improvements to users. It's designed to show once per user and is dismissable.

## Features

### 🎨 Apple-Inspired Design
- Minimalist and elegant design following Apple's design principles
- Smooth fade-in animation with scale transformation
- Soft shadow and rounded corners (radius: 2xl)
- Clean typography hierarchy
- Light color scheme with excellent contrast

### 🔄 One-Time Display
- Uses browser `localStorage` to persist dismissal state
- Shows only once per user, per browser/device
- Optional `resetModal()` function to show again for testing

### ♿ Accessibility
- Proper ARIA labels and attributes
- Keyboard accessible close button
- Focus management
- Semantic HTML structure

### 📱 Responsive
- Adapts to different screen sizes
- Works on mobile with appropriate padding
- Fixed positioning for z-index management

## Components

### WhatsNewModal Component

The main component that renders the modal.

```tsx
import { WhatsNewModal, useWhatsNewModal } from "@/components/ui/whats-new-modal";

// In your component:
const { showModal, handleDismiss } = useWhatsNewModal();

<WhatsNewModal isOpen={showModal} onClose={handleDismiss} />
```

**Props:**
- `isOpen` (boolean): Controls whether the modal is visible
- `onClose` (function): Callback function when modal is dismissed

### useWhatsNewModal Hook

Custom hook for managing the modal's visibility state.

```tsx
const { showModal, handleDismiss, resetModal } = useWhatsNewModal();
```

**Returns:**
- `showModal` (boolean): Current visibility state
- `handleDismiss` (): Function to dismiss modal and persist to localStorage
- `resetModal` (): Function to reset localStorage and show modal again (for testing)

## Usage

### Basic Implementation

In `DialogueManager.tsx`:

```tsx
import { WhatsNewModal, useWhatsNewModal } from "@/components/ui/whats-new-modal";

function DialogueManager() {
  const { showModal, handleDismiss } = useWhatsNewModal();

  return (
    <>
      {/* Your component content */}
      <WhatsNewModal isOpen={showModal} onClose={handleDismiss} />
    </>
  );
}
```

### Testing

To test the modal in development:

1. **First time visit**: Modal appears automatically
2. **Subsequent visits**: Modal is hidden (unless localStorage is cleared)
3. **Reset for testing**: Open browser console and run:
   ```javascript
   localStorage.removeItem('whats_new_modal_dismissed');
   location.reload();
   ```

## Design Details

### Animation
- **Duration**: 300ms smooth transition
- **Effect**: Scale up (95% → 100%) + fade in (0% → 100%)
- **Backdrop**: Gradually fades in from transparent to black/30

### Colors
- **Background**: White (`bg-white`)
- **Text**: Dark gray (`text-gray-900` for heading, `text-gray-600` for body)
- **Button**: Blue (`bg-blue-600` with hover state `bg-blue-700`)
- **Backdrop**: Semi-transparent black (`bg-black/30`)

### Typography
- **Heading**: 2xl, semibold, tight tracking
- **Body**: Base size, regular weight, relaxed line-height
- **Button**: Small, semibold

### Spacing
- **Container padding**: px-8 py-8
- **Gap between elements**: mb-6, mt-8
- **Close button**: right-4 top-4

## Storage

The modal uses `localStorage` with the key `whats_new_modal_dismissed` to track dismissal state:
- Value `"true"`: User has dismissed the modal
- Value not set or other: User hasn't seen/dismissed the modal

## Customization

To customize the message, update the content in `WhatsNewModal` component:

```tsx
<p className="text-base leading-relaxed text-gray-600">
  Your new message here
</p>
```

To customize the button text:

```tsx
<button
  type="button"
  onClick={onClose}
  className="..."
>
  Your Button Text
</button>
```

## Browser Compatibility

- Works in all modern browsers with localStorage support
- Gracefully degrades if localStorage is disabled (modal won't persist dismissal)
- CSS animations use standard Tailwind utilities

## Performance

- Minimal impact on performance
- Single useEffect hook for localStorage check
- Conditional rendering with early return
- No expensive computations

## Accessibility Checklist

✅ Close button has `aria-label`  
✅ Modal has proper z-index layering  
✅ Backdrop is marked with `aria-hidden`  
✅ Semantic button elements with `type="button"`  
✅ Proper focus management  
✅ High contrast text (WCAG AA compliant)  
✅ Keyboard dismissible (Escape key via backdrop click)
