import { useApp } from './context/AppContext';
import { Sidebar } from './components/layout/Sidebar';
import { Topbar } from './components/layout/Topbar';
import { Landing } from './pages/Landing';
import { Login } from './pages/Login';
import { Register } from './pages/Register';
import { ForgotPassword } from './pages/ForgotPassword';
import { Dashboard } from './pages/Dashboard';
import { Upload } from './pages/Upload';
import { Understand } from './pages/Understand';
import { Requirements } from './pages/Requirements';
import { Processing } from './pages/Processing';
import { Results } from './pages/Results';
import { Export } from './pages/Export';
import { MyData } from './pages/MyData';
import { Profile } from './pages/Profile';
import { ProductIntelligence } from './pages/ProductIntelligence';
import { Validation } from './pages/Validation';

export function App() {
  const { activeTab } = useApp();

  // Public Fullscreen Pages without App Shell
  if (activeTab === 'landing') {
    return <Landing />;
  }
  if (activeTab === 'login') {
    return <Login />;
  }
  if (activeTab === 'register') {
    return <Register />;
  }
  if (activeTab === 'forgot-password') {
    return <ForgotPassword />;
  }

  const getPageMeta = () => {
    switch (activeTab) {
      case 'dashboard':
        return {
          title: 'Catalog Overview & Intelligence',
          subtitle: 'Manage uploaded industrial product catalogs and start new transformations.',
        };
      case 'jobs':
        return {
          title: 'My Catalogs',
          subtitle: 'Inspect processed catalogs, product records, and generated exports.',
        };
      case 'upload':
        return {
          title: 'Start with your product catalog',
          subtitle: 'Upload CSV or Excel files. SPECra automatically detects columns and structure.',
        };
      case 'understand':
        return {
          title: 'Catalog Structure & Mapping',
          subtitle: 'SPECra understands column semantics without predefined rigid templates.',
        };
      case 'requirements':
        return {
          title: 'What would you like SPECra to find?',
          subtitle: 'Specify attributes, dimensions, and packaging requirements in natural language.',
        };
      case 'process':
      case 'pipeline':
        return {
          title: 'SPECra is understanding your catalog',
          subtitle: 'Extracting product specifications, standardizing units, and verifying evidence.',
        };
      case 'results':
        return {
          title: 'Your product intelligence is ready',
          subtitle: 'Review prepared specifications, inspect source quotes, and download data.',
        };
      case 'validation':
        return {
          title: 'How reliable is your catalog?',
          subtitle: 'Data quality verification score and physical consistency audit.',
        };
      case 'export':
        return {
          title: 'Your data is ready to use',
          subtitle: 'Download structured CSV, Excel, or enterprise UniHack 252-column datasets.',
        };
      case 'profile':
        return {
          title: 'Workspace Profile & Security',
          subtitle: 'Personal information, organization settings, and credential control.',
        };
      default:
        return {
          title: 'SPECra AI Product Intelligence',
          subtitle: 'Turn messy product data into intelligence.',
        };
    }
  };

  const pageMeta = getPageMeta();

  return (
    <div className="flex h-screen bg-[#07090e] text-slate-100 overflow-hidden selection:bg-cyan-500 selection:text-slate-950 font-sans">
      {/* Left Navigation Sidebar */}
      <Sidebar />

      {/* Main Content Area with Sticky Topbar */}
      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <Topbar title={pageMeta.title} subtitle={pageMeta.subtitle} />

        <main className="flex-1 p-6 md:p-8">
          {activeTab === 'dashboard' && <Dashboard />}
          {activeTab === 'jobs' && <MyData />}
          {activeTab === 'upload' && <Upload />}
          {activeTab === 'understand' && <Understand />}
          {activeTab === 'requirements' && <Requirements />}
          {(activeTab === 'process' || activeTab === 'pipeline') && <Processing />}
          {activeTab === 'results' && <Results />}
          {activeTab === 'intelligence' && <ProductIntelligence />}
          {activeTab === 'validation' && <Validation />}
          {activeTab === 'export' && <Export />}
          {activeTab === 'profile' && <Profile />}
        </main>
      </div>
    </div>
  );
}
