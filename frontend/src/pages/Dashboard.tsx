import React, { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import apiClient from '../api/client';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import Button from '../components/ui/Button';
import { 
  ShieldAlert, 
  CheckCircle, 
  Terminal, 
  Activity, 
  Upload, 
  FileCode, 
  ArrowRight,
  ShieldCheck,
  FolderOpen,
  Search,
  Filter,
  AlertTriangle,
  FileText
} from 'lucide-react';

interface ReportSummary {
  id: string;
  submission_id: string;
  summary: string;
  score: number;
  created_at: string;
}

interface Finding {
  id: string;
  report_id: string;
  file_path: string;
  line_number: number;
  severity: string;
  category: string;
  title: string;
  description: string;
  recommendation: string;
}

export const Dashboard: React.FC = () => {
  const { activeProject, projects } = useAuth();
  const [reports, setReports] = useState<ReportSummary[]>([]);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [loading, setLoading] = useState(false);
  
  // Search & Filter States
  const [reportSearch, setReportSearch] = useState('');
  const [findingSeverityFilter, setFindingSeverityFilter] = useState('All');
  const [findingCategoryFilter, setFindingCategoryFilter] = useState('All');
  
  const navigate = useNavigate();

  useEffect(() => {
    const fetchDashboardData = async () => {
      if (!activeProject) return;
      setLoading(true);
      try {
        const reportsRes = await apiClient.get<ReportSummary[]>(`/reports/project/${activeProject.id}`);
        setReports(reportsRes.data);
        
        const findingsRes = await apiClient.get<Finding[]>(`/reports/project/${activeProject.id}/findings`);
        setFindings(findingsRes.data);
      } catch (err) {
        console.error('Failed to load dashboard parameters', err);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, [activeProject]);

  if (projects.length === 0) {
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center text-center p-8">
        <FolderOpen className="h-16 w-16 text-muted-foreground/60 mb-4 animate-bounce" />
        <h2 className="text-xl font-bold font-sans">No workspace projects found</h2>
        <p className="text-muted-foreground mt-2 max-w-sm">
          Create a workspace project container to deploy code reviews and static analysis security scans.
        </p>
        <Link to="/settings" className="mt-6">
          <Button>Create Project Container</Button>
        </Link>
      </div>
    );
  }

  // 1. Statistics Calculations
  const totalScans = reports.length;
  const averageScore = totalScans > 0 
    ? Math.round(reports.reduce((acc, curr) => acc + curr.score, 0) / totalScans) 
    : 100;
  
  const totalSecurity = findings.filter(f => f.category === 'Security').length;
  const totalQuality = findings.filter(f => f.category === 'Code Quality').length;

  const criticalCount = findings.filter(f => f.severity === 'Critical').length;
  const highCount = findings.filter(f => f.severity === 'High').length;
  const mediumCount = findings.filter(f => f.severity === 'Medium').length;
  const lowCount = findings.filter(f => f.severity === 'Low').length;

  // Determine Workspace Health status
  let healthStatus = 'Secure';
  let healthColor = 'text-green-500 bg-green-500/10 border-green-500/20';
  if (criticalCount > 0 || averageScore < 70) {
    healthStatus = 'Critical Risk';
    healthColor = 'text-red-500 bg-red-500/10 border-red-500/20';
  } else if (highCount > 0 || averageScore < 85) {
    healthStatus = 'Warning';
    healthColor = 'text-yellow-500 bg-yellow-500/10 border-yellow-500/20';
  }

  // 2. SVG Donut Segment Calculation
  const donutTotal = criticalCount + highCount + mediumCount + lowCount;
  const donutRadius = 35;
  const donutCircumference = 2 * Math.PI * donutRadius; // ~219.9
  
  const calculateStrokeDash = (count: number) => {
    if (donutTotal === 0) return `0 ${donutCircumference}`;
    const value = (count / donutTotal) * donutCircumference;
    return `${value} ${donutCircumference}`;
  };

  const getStrokeOffset = (prevCountsSum: number) => {
    if (donutTotal === 0) return 0;
    return -((prevCountsSum / donutTotal) * donutCircumference);
  };

  // 3. Search & Filters filtering
  const filteredReports = reports.filter(rep => 
    rep.summary.toLowerCase().includes(reportSearch.toLowerCase()) ||
    rep.id.toLowerCase().includes(reportSearch.toLowerCase())
  );

  const filteredFindings = findings.filter(find => {
    const sevMatch = findingSeverityFilter === 'All' || find.severity === findingSeverityFilter;
    const catMatch = findingCategoryFilter === 'All' || find.category === findingCategoryFilter;
    return sevMatch && catMatch;
  });

  return (
    <div className="space-y-8 animate-fade-in pb-12">
      {/* Intro Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-extrabold tracking-tight font-sans text-foreground">
            System Workspace
          </h2>
          <p className="text-sm text-muted-foreground mt-1">
            Monitoring security and code health in container: <strong>{activeProject?.name}</strong>
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link to="/upload">
            <Button variant="outline" size="sm" className="flex items-center gap-2">
              <Upload className="h-4 w-4" />
              <span>Upload Archive</span>
            </Button>
          </Link>
          <Link to="/paste">
            <Button size="sm" className="flex items-center gap-2">
              <FileCode className="h-4 w-4" />
              <span>Paste Code</span>
            </Button>
          </Link>
        </div>
      </div>

      {/* Numerical Indicators Dashboard */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <Card className="hover:-translate-y-1 transition-all">
          <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
            <CardTitle className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Total Audits
            </CardTitle>
            <Terminal className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-extrabold font-sans">{totalScans}</div>
            <p className="text-[10px] text-muted-foreground mt-1 font-medium">Scans submitted to date</p>
          </CardContent>
        </Card>

        <Card className="hover:-translate-y-1 transition-all">
          <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
            <CardTitle className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Average Score
            </CardTitle>
            <ShieldCheck className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-extrabold font-sans text-green-500">{averageScore}/100</div>
            <p className="text-[10px] text-muted-foreground mt-1 font-medium">Project code health metrics</p>
          </CardContent>
        </Card>

        <Card className="hover:-translate-y-1 transition-all">
          <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
            <CardTitle className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Security Flagged
            </CardTitle>
            <ShieldAlert className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-extrabold font-sans text-red-500">{totalSecurity}</div>
            <p className="text-[10px] text-muted-foreground mt-1 font-medium">vulnerability findings detected</p>
          </CardContent>
        </Card>

        <Card className="hover:-translate-y-1 transition-all">
          <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
            <CardTitle className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Workspace Health
            </CardTitle>
            <Activity className="h-4 w-4 text-primary animate-pulse" />
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <span className={`inline-flex items-center justify-center rounded-full px-2.5 py-0.5 text-xs font-bold border ${healthColor}`}>
                {healthStatus}
              </span>
            </div>
            <p className="text-[10px] text-muted-foreground mt-2 font-medium">Aggregated security status</p>
          </CardContent>
        </Card>
      </div>

      {/* CHARTS CONTAINER GRID */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Severity Donut Pie Chart (lg:col-span-5) */}
        <Card className="lg:col-span-5 flex flex-col">
          <CardHeader>
            <CardTitle>Vulnerabilities Severity</CardTitle>
            <CardDescription>Breakdown of security issues inside active submissions.</CardDescription>
          </CardHeader>
          <CardContent className="flex-1 flex flex-col items-center justify-center py-6">
            {donutTotal === 0 ? (
              <div className="text-center py-8 text-muted-foreground flex flex-col items-center gap-2">
                <CheckCircle className="h-10 w-10 text-green-500/80" />
                <span className="text-xs font-semibold">No issues flagged in database</span>
              </div>
            ) : (
              <div className="w-full flex flex-col sm:flex-row items-center justify-around gap-6">
                
                {/* SVG Donut Chart */}
                <div className="relative w-36 h-36">
                  <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                    <circle
                      cx="50"
                      cy="50"
                      r={donutRadius}
                      fill="transparent"
                      stroke="var(--border)"
                      strokeWidth="10"
                    />
                    
                    {/* Critical (Red) */}
                    <circle
                      cx="50"
                      cy="50"
                      r={donutRadius}
                      fill="transparent"
                      stroke="#ef4444"
                      strokeWidth="10"
                      strokeDasharray={calculateStrokeDash(criticalCount)}
                      strokeDashoffset={getStrokeOffset(0)}
                    />
                    {/* High (Orange) */}
                    <circle
                      cx="50"
                      cy="50"
                      r={donutRadius}
                      fill="transparent"
                      stroke="#f97316"
                      strokeWidth="10"
                      strokeDasharray={calculateStrokeDash(highCount)}
                      strokeDashoffset={getStrokeOffset(criticalCount)}
                    />
                    {/* Medium (Yellow) */}
                    <circle
                      cx="50"
                      cy="50"
                      r={donutRadius}
                      fill="transparent"
                      stroke="#eab308"
                      strokeWidth="10"
                      strokeDasharray={calculateStrokeDash(mediumCount)}
                      strokeDashoffset={getStrokeOffset(criticalCount + highCount)}
                    />
                    {/* Low (Blue) */}
                    <circle
                      cx="50"
                      cy="50"
                      r={donutRadius}
                      fill="transparent"
                      stroke="#3b82f6"
                      strokeWidth="10"
                      strokeDasharray={calculateStrokeDash(lowCount)}
                      strokeDashoffset={getStrokeOffset(criticalCount + highCount + mediumCount)}
                    />
                  </svg>
                  
                  {/* Inside Center Text */}
                  <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
                    <span className="text-xl font-extrabold">{donutTotal}</span>
                    <span className="text-[8px] uppercase tracking-wider text-muted-foreground">Findings</span>
                  </div>
                </div>

                {/* Donut Labels */}
                <div className="space-y-2 text-xs">
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 bg-red-500 rounded-full"></span>
                    <span className="font-medium text-foreground">Critical ({criticalCount})</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 bg-orange-500 rounded-full"></span>
                    <span className="font-medium text-foreground">High ({highCount})</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 bg-yellow-500 rounded-full"></span>
                    <span className="font-medium text-foreground">Medium ({mediumCount})</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 bg-blue-500 rounded-full"></span>
                    <span className="font-medium text-foreground">Low ({lowCount})</span>
                  </div>
                </div>

              </div>
            )}
          </CardContent>
        </Card>

        {/* Issue Score Trend (lg:col-span-7) */}
        <Card className="lg:col-span-7">
          <CardHeader>
            <CardTitle>Audit Run Trends</CardTitle>
            <CardDescription>Visual score distribution tracking recent code submission evaluations.</CardDescription>
          </CardHeader>
          <CardContent className="h-44 flex items-end justify-between gap-4 pb-4 px-6 border-b border-border/40">
            {reports.length === 0 ? (
              <div className="w-full text-center py-12 text-xs text-muted-foreground font-semibold">
                Submit raw code files to trace progress scores.
              </div>
            ) : (
              reports.slice(-8).map((rep, idx) => (
                <div key={rep.id} className="flex-1 flex flex-col items-center gap-2 group cursor-pointer" onClick={() => navigate(`/results?report=${rep.id}`)}>
                  {/* Tooltip on hover */}
                  <span className="opacity-0 group-hover:opacity-100 transition-opacity text-[9px] bg-foreground text-background px-1.5 py-0.5 rounded font-bold">
                    {rep.score}
                  </span>
                  
                  {/* Bar block */}
                  <div 
                    style={{ height: `${Math.max(12, rep.score)}px` }}
                    className={`w-full rounded-t transition-all max-h-[120px] ${
                      rep.score >= 90 
                        ? 'bg-green-500 group-hover:bg-green-600' 
                        : rep.score >= 75 
                        ? 'bg-yellow-500 group-hover:bg-yellow-600' 
                        : 'bg-red-500 group-hover:bg-red-600'
                    }`}
                  />
                  
                  <span className="text-[9px] font-mono text-muted-foreground font-semibold">
                    R-{rep.id.substring(0, 4)}
                  </span>
                </div>
              ))
            )}
          </CardContent>
        </Card>

      </div>

      {/* DATABASE TABLES / SEARCH FILTER MATRIX */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* RECENT REVIEWS LOGGER WITH SEARCH */}
        <Card className="lg:col-span-6">
          <CardHeader className="space-y-3">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <div>
                <CardTitle>Recent Reviews</CardTitle>
                <CardDescription>Evaluation runs history logs.</CardDescription>
              </div>
              
              {/* Search Bar */}
              <div className="relative">
                <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
                <input
                  type="text"
                  placeholder="Search summaries..."
                  value={reportSearch}
                  onChange={(e) => setReportSearch(e.target.value)}
                  className="bg-muted/40 border border-border rounded-lg pl-8 pr-3 py-1.5 text-xs text-foreground focus:outline-none focus:border-primary w-full sm:w-44"
                />
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex h-36 items-center justify-center">
                <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent"></div>
              </div>
            ) : filteredReports.length === 0 ? (
              <div className="text-center py-10 text-xs text-muted-foreground font-semibold">
                No matching reports.
              </div>
            ) : (
              <div className="space-y-4 max-h-[350px] overflow-y-auto pr-1">
                {filteredReports.map((report) => (
                  <div key={report.id} className="flex items-center justify-between p-3 bg-muted/20 border border-border/50 rounded-xl group hover:border-primary/40 transition-colors">
                    <div className="space-y-1 flex-1 min-w-0 pr-3">
                      <p className="text-xs font-semibold text-foreground truncate">
                        Run - {report.id.substring(0, 8)}
                      </p>
                      <p className="text-[11px] text-muted-foreground truncate">
                        {report.summary.replace(/#/g, '')}
                      </p>
                      <p className="text-[9px] text-muted-foreground">
                        {new Date(report.created_at).toLocaleString()}
                      </p>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-bold ${
                        report.score >= 90 
                          ? 'bg-green-500/10 text-green-500 border border-green-500/20' 
                          : 'bg-red-500/10 text-red-500 border border-red-500/20'
                      }`}>
                        Score: {report.score}
                      </span>
                      <button
                        onClick={() => navigate(`/results?report=${report.id}`)}
                        className="p-1 border border-border rounded-lg bg-card hover:bg-muted transition-colors"
                      >
                        <ArrowRight className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* LATEST FINDINGS MATRIX WITH SEVERITY FILTERS */}
        <Card className="lg:col-span-6">
          <CardHeader className="space-y-3">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <div>
                <CardTitle>Latest Findings</CardTitle>
                <CardDescription>Code issue occurrences across project repository files.</CardDescription>
              </div>
              
              {/* Dropdown Filters */}
              <div className="flex items-center gap-2">
                <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                  <Filter className="h-3 w-3" />
                  <span>Filters:</span>
                </div>
                <select
                  value={findingSeverityFilter}
                  onChange={(e) => setFindingSeverityFilter(e.target.value)}
                  className="bg-muted/40 border border-border rounded-lg px-2 py-1 text-xs text-foreground focus:outline-none"
                >
                  <option value="All">All Severities</option>
                  <option value="Critical">Critical</option>
                  <option value="High">High</option>
                  <option value="Medium">Medium</option>
                  <option value="Low">Low</option>
                </select>
                <select
                  value={findingCategoryFilter}
                  onChange={(e) => setFindingCategoryFilter(e.target.value)}
                  className="bg-muted/40 border border-border rounded-lg px-2 py-1 text-xs text-foreground focus:outline-none"
                >
                  <option value="All">All Categories</option>
                  <option value="Security">Security</option>
                  <option value="Code Quality">Code Quality</option>
                </select>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex h-36 items-center justify-center">
                <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent"></div>
              </div>
            ) : filteredFindings.length === 0 ? (
              <div className="text-center py-10 text-xs text-muted-foreground font-semibold">
                No matching findings.
              </div>
            ) : (
              <div className="space-y-3 max-h-[350px] overflow-y-auto pr-1">
                {filteredFindings.map((find) => (
                  <div 
                    key={find.id} 
                    className="p-3 bg-muted/20 border border-border/50 rounded-xl flex items-start gap-3 cursor-pointer hover:border-primary/40 transition-colors"
                    onClick={() => navigate(`/results?report=${find.report_id}`)}
                  >
                    <div className="mt-0.5">
                      {find.category === 'Security' ? (
                        <ShieldAlert className="h-4 w-4 text-red-500" />
                      ) : (
                        <AlertTriangle className="h-4 w-4 text-yellow-500" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-1">
                        <span className={`inline-flex items-center rounded-full px-1.5 py-0.2 text-[9px] font-bold border ${
                          find.severity === 'Critical' ? 'bg-red-500/10 text-red-500 border-red-500/20' : 'bg-blue-500/10 text-blue-500 border-blue-500/20'
                        }`}>
                          {find.severity}
                        </span>
                        <span className="text-[9px] text-muted-foreground truncate max-w-[150px]">
                          {find.file_path.split('/').pop()}:L{find.line_number}
                        </span>
                      </div>
                      <p className="text-xs font-bold text-foreground truncate">{find.title}</p>
                      <p className="text-[11px] text-muted-foreground truncate mt-0.5">{find.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

      </div>

    </div>
  );
};
export default Dashboard;
