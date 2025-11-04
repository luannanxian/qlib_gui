# 前端模块 1: 用户引导与模式管理

## 模块概述

前端用户引导和模式管理模块,提供新手/专家模式切换UI、引导流程组件和帮助系统界面。

## 核心职责

1. **模式切换UI**: 新手/专家模式切换组件
2. **引导流程**: 分步引导组件,进度追踪
3. **帮助系统**: 帮助文档弹窗,FAQ页面
4. **用户偏好**: 偏好设置界面

## 目录结构

```
user-onboarding/
├── components/          # UI组件
│   ├── ModeToggle.tsx       # 模式切换组件
│   ├── OnboardingWizard.tsx # 引导向导
│   ├── TutorialStep.tsx     # 教程步骤
│   ├── HelpButton.tsx       # 帮助按钮
│   ├── HelpPanel.tsx        # 帮助面板
│   └── FAQSection.tsx       # FAQ部分
├── hooks/               # React Hooks
│   ├── useUserMode.ts       # 用户模式hook
│   ├── useOnboarding.ts     # 引导流程hook
│   └── useHelp.ts           # 帮助系统hook
├── store/               # 状态管理
│   ├── modeStore.ts         # 模式状态
│   └── onboardingStore.ts   # 引导状态
├── api/                 # API调用
│   └── onboardingApi.ts
├── types/               # TypeScript类型
│   └── index.ts
├── constants/           # 常量
│   └── tutorials.ts
└── Claude.md            # 本文档
```

## 核心组件

### 1. ModeToggle 组件
```typescript
interface ModeToggleProps {
  mode: 'beginner' | 'expert';
  onChange: (mode: 'beginner' | 'expert') => void;
  className?: string;
}

export function ModeToggle({ mode, onChange }: ModeToggleProps) {
  return (
    <div className="mode-toggle">
      <button
        className={mode === 'beginner' ? 'active' : ''}
        onClick={() => onChange('beginner')}
      >
        新手模式
      </button>
      <button
        className={mode === 'expert' ? 'active' : ''}
        onClick={() => onChange('expert')}
      >
        专家模式
      </button>
    </div>
  );
}
```

### 2. OnboardingWizard 组件
```typescript
interface OnboardingStep {
  id: string;
  title: string;
  description: string;
  targetElement?: string;
  action?: () => void;
}

interface OnboardingWizardProps {
  steps: OnboardingStep[];
  currentStep: number;
  onNext: () => void;
  onPrev: () => void;
  onSkip: () => void;
  onComplete: () => void;
}

export function OnboardingWizard({
  steps,
  currentStep,
  onNext,
  onPrev,
  onSkip,
  onComplete
}: OnboardingWizardProps) {
  const step = steps[currentStep];
  const isLastStep = currentStep === steps.length - 1;

  return (
    <div className="onboarding-wizard">
      <div className="step-content">
        <h3>{step.title}</h3>
        <p>{step.description}</p>
      </div>
      <div className="step-actions">
        {currentStep > 0 && <button onClick={onPrev}>上一步</button>}
        {!isLastStep && <button onClick={onNext}>下一步</button>}
        {isLastStep && <button onClick={onComplete}>完成</button>}
        <button onClick={onSkip}>跳过</button>
      </div>
      <div className="step-progress">
        {currentStep + 1} / {steps.length}
      </div>
    </div>
  );
}
```

### 3. HelpPanel 组件
```typescript
interface HelpTopic {
  id: string;
  title: string;
  content: string;
  category: string;
}

interface HelpPanelProps {
  topic?: string;
  onClose: () => void;
}

export function HelpPanel({ topic, onClose }: HelpPanelProps) {
  const { data: helpContent } = useHelp(topic);

  return (
    <div className="help-panel">
      <div className="help-header">
        <h2>帮助</h2>
        <button onClick={onClose}>×</button>
      </div>
      <div className="help-content">
        {helpContent && (
          <>
            <h3>{helpContent.title}</h3>
            <div dangerouslySetInnerHTML={{ __html: helpContent.content }} />
          </>
        )}
      </div>
    </div>
  );
}
```

## Hooks

### useUserMode
```typescript
export function useUserMode() {
  const [mode, setMode] = useState<'beginner' | 'expert'>('beginner');
  const [preferences, setPreferences] = useState<UserPreferences | null>(null);

  // 从后端加载用户模式
  useEffect(() => {
    async function loadMode() {
      const data = await api.getUserMode();
      setMode(data.mode);
      setPreferences(data.preferences);
    }
    loadMode();
  }, []);

  // 切换模式
  const toggleMode = async (newMode: 'beginner' | 'expert') => {
    await api.updateUserMode(newMode);
    setMode(newMode);
  };

  return { mode, preferences, toggleMode };
}
```

### useOnboarding
```typescript
export function useOnboarding() {
  const [currentStep, setCurrentStep] = useState(0);
  const [completed, setCompleted] = useState(false);
  const [steps, setSteps] = useState<OnboardingStep[]>([]);

  useEffect(() => {
    async function loadSteps() {
      const data = await api.getOnboardingSteps();
      setSteps(data);
    }
    loadSteps();
  }, []);

  const nextStep = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const prevStep = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const complete = async () => {
    await api.updateOnboardingProgress({ completed: true });
    setCompleted(true);
  };

  const skip = async () => {
    await api.updateOnboardingProgress({ skipped: true });
    setCompleted(true);
  };

  return {
    steps,
    currentStep,
    completed,
    nextStep,
    prevStep,
    complete,
    skip
  };
}
```

## 状态管理

### Zustand Store
```typescript
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface ModeState {
  mode: 'beginner' | 'expert';
  showTooltips: boolean;
  completedGuides: string[];
  setMode: (mode: 'beginner' | 'expert') => void;
  toggleTooltips: () => void;
  markGuideComplete: (guideId: string) => void;
}

export const useModeStore = create<ModeState>()(
  persist(
    (set) => ({
      mode: 'beginner',
      showTooltips: true,
      completedGuides: [],
      setMode: (mode) => set({ mode }),
      toggleTooltips: () => set((state) => ({ showTooltips: !state.showTooltips })),
      markGuideComplete: (guideId) =>
        set((state) => ({
          completedGuides: [...state.completedGuides, guideId]
        }))
    }),
    {
      name: 'user-mode-storage'
    }
  )
);
```

## API调用

```typescript
export const onboardingApi = {
  getUserMode: async () => {
    const response = await fetch('/api/user/mode');
    return response.json();
  },

  updateUserMode: async (mode: 'beginner' | 'expert') => {
    const response = await fetch('/api/user/mode', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mode })
    });
    return response.json();
  },

  getOnboardingSteps: async () => {
    const response = await fetch('/api/guide/steps');
    return response.json();
  },

  updateOnboardingProgress: async (progress: any) => {
    const response = await fetch('/api/guide/progress', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(progress)
    });
    return response.json();
  },

  getHelpTopic: async (topicId: string) => {
    const response = await fetch(`/api/help/topics/${topicId}`);
    return response.json();
  }
};
```

## 技术要点

### 引导库
- **react-joyride**: 分步引导
- **driver.js**: 高亮引导
- **intro.js**: 交互式教程

### 状态管理
- **Zustand**: 轻量级状态管理
- **localStorage**: 本地持久化

### UI组件
- **Ant Design**: Modal, Steps, Tooltip
- **Headless UI**: 无样式组件
- **Radix UI**: 可访问组件

## 集成示例

```typescript
// 在App.tsx中集成
function App() {
  const { mode } = useUserMode();
  const { completed, steps, currentStep, nextStep, prevStep, complete, skip } = useOnboarding();

  return (
    <div className={`app mode-${mode}`}>
      {!completed && (
        <OnboardingWizard
          steps={steps}
          currentStep={currentStep}
          onNext={nextStep}
          onPrev={prevStep}
          onComplete={complete}
          onSkip={skip}
        />
      )}
      {/* 其他内容 */}
    </div>
  );
}
```

## 测试要点

- 模式切换功能测试
- 引导流程完整性测试
- 帮助内容加载测试
- 本地存储持久化测试

## 注意事项

1. 引导流程不应阻塞用户操作
2. 支持随时跳过和重新开始
3. 帮助内容支持搜索
4. 模式切换平滑过渡
5. 移动端适配
