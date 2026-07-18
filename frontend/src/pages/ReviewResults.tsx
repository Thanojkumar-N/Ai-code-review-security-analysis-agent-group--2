import React, { useEffect, useState, useRef } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import apiClient from '../api/client';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import Button from '../components/ui/Button';
import { 
  ShieldAlert, 
  Terminal, 
  ChevronRight, 
  AlertTriangle, 
  CheckCircle,
  HelpCircle,
  FileCode,
  ArrowLeft,
  Settings,
  MessageSquare,
  Send,
  X,
  Bot,
  Download,
  Share2,
  BookOpen,
  Code2,
  FileText
} from 'lucide-react';

interface Finding {
  id: string;
  file_path: string;
  line_number: number;
  severity: string;
  category: string;
  title: string;
  description: string;
  recommendation: string;
  code_snippet: string;
  created_at: string;
}

interface ReportDetails {
  id: string;
  submission_id: string;
  summary: string;
  score: number;
  created_at: string;
  findings: Finding[];
}

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export const ReviewResults: React.FC = () => {
  const { activeProject } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const reportId = searchParams.get('report');
  
  const [report, setReport] = useState<ReportDetails | null>(null);
  const [reportsList, setReportsList] = useState<ReportDetails[]>([]);
  const [selectedFinding, setSelectedFinding] = useState<Finding | null>(null);
  const [loading, setLoading] = useState(false);
  const [listLoading, setListLoading] = useState(false);

  // Active Remediation Tab state
  const [remediationTab, setRemediationTab] = useState<'explanation' | 'remediation' | 'code' | 'reference'>('explanation');

  // Share Notification State
  const [shareSuccess, setShareSuccess] = useState(false);
  const [downloadDropdown, setDownloadDropdown] = useState(false);

  // Chat Assistant States
  const [chatOpen, setChatOpen] = useState(false);
  const [chatInput, setChatInput] = useState('');
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatLoading, setChatLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (chatOpen) {
      scrollToBottom();
    }
  }, [chatMessages, chatOpen]);

  // Fetch report list if no report ID is active in query
  useEffect(() => {
    const fetchReportsList = async () => {
      if (reportId || !activeProject) return;
      setListLoading(true);
      try {
        const response = await apiClient.get<ReportDetails[]>(`/reports/project/${activeProject.id}`);
        setReportsList(response.data);
      } catch (err) {
        console.error('Failed to load project reports list', err);
      } finally {
        setListLoading(false);
      }
    };

    fetchReportsList();
  }, [reportId, activeProject]);

  // Fetch specific report details if active
  useEffect(() => {
    const fetchReportDetails = async () => {
      if (!reportId) {
        setReport(null);
        setSelectedFinding(null);
        setChatMessages([]);
        return;
      }
      setLoading(true);
      try {
        const response = await apiClient.get<ReportDetails>(`/reports/${reportId}`);
        setReport(response.data);
        if (response.data.findings.length > 0) {
          setSelectedFinding(response.data.findings[0]);
        }
        setChatMessages([
          { role: 'assistant', content: 'Hello! I am your Conversational Code Assistant. I can help explain these code quality issues, recommend solid adjustments, or answer questions about secure coding standards. Ask me anything!' }
        ]);
      } catch (err) {
        console.error('Failed to load report details', err);
        setReport(null);
      } finally {
        setLoading(false);
      }
    };

    fetchReportDetails();
  }, [reportId]);

  // Handle Share link copying
  const handleShareReport = () => {
    navigator.clipboard.writeText(window.location.href);
    setShareSuccess(true);
    setTimeout(() => setShareSuccess(false), 3000);
  };

  // Trigger report download blobs
  const handleDownloadExport = async (type: 'JSON' | 'CSV') => {
    if (!reportId) return;
    try {
      const response = await apiClient.post(`/reports/${reportId}/export`, {
        report_id: reportId,
        export_type: type
      });
      
      const fileData = JSON.stringify(response.data, null, 2);
      const blob = new Blob([fileData], { type: 'application/json' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `security_report_${reportId.substring(0, 8)}.${type.toLowerCase()}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      setDownloadDropdown(false);
    } catch (err) {
      console.error('Failed to export report document', err);
    }
  };

  // Handle chat submission
  const handleSendChat = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim() || chatLoading || !reportId) return;

    const userMessage: ChatMessage = { role: 'user', content: chatInput };
    setChatMessages((prev) => [...prev, userMessage]);
    setChatInput('');
    setChatLoading(true);

    try {
      const payload = {
        message: userMessage.content,
        conversation_history: chatMessages.slice(1)
      };
      
      const response = await apiClient.post<{ response: string }>(`/reports/${reportId}/chat`, payload);
      setChatMessages((prev) => [...prev, { role: 'assistant', content: response.data.response }]);
    } catch (err) {
      console.error('Chat error', err);
      setChatMessages((prev) => [...prev, { role: 'assistant', content: 'Sorry, I encountered an error connecting to the conversation assistant engine.' }]);
    } finally {
      setChatLoading(false);
    }
  };

  // Color mapping based on severity levels
  const severityColors: { [key: string]: string } = {
    Critical: 'text-red-500 bg-red-500/10 border-red-500/20',
    High: 'text-orange-500 bg-orange-500/10 border-orange-500/20',
    Medium: 'text-yellow-500 bg-yellow-500/10 border-yellow-500/20',
    Low: 'text-blue-500 bg-blue-500/10 border-blue-500/20',
    Info: 'text-green-500 bg-green-500/10 border-green-500/20',
  };

  // Recommendation section Markdown extractor
  const renderRemediationTabs = (recText: string) => {
    if (!recText) return null;
    
    const explanationMatch = recText.match(/### Explanation\n([\s\S]*?)(?=\n###|$)/);
    const recMatch = recText.match(/### Secure Coding Recommendation\n([\s\S]*?)(?=\n###|$)/);
    const refMatch = recText.match(/### Reference\n([\s\S]*?)(?=\n###|$)/);
    const beforeMatch = recText.match(/\*\*Insecure Code \(Before\)\*\*:\n```\n([\s\S]*?)\n```/);
    const afterMatch = recText.match(/\*\*Secure Correction \(After\)\*\*:\n```\n([\s\S]*?)\n```/);
    
    const explanation = explanationMatch ? explanationMatch[1].trim() : 'Static scan security summary.';
    const recommendation = recMatch ? recMatch[1].trim() : 'Apply standard programming rules to validate variables.';
    const reference = refMatch ? refMatch[1].trim().replace(/^- /, '') : 'CWE guidelines reference.';
    const beforeCode = beforeMatch ? beforeMatch[1] : '';
    const afterCode = afterMatch ? afterMatch[1] : '';

    return (
      <div className="space-y-4">
        
        {/* Navigation Tabs Bar */}
        <div className="flex border-b border-border/60 text-xs font-semibold gap-4 overflow-x-auto">
          <button 
            onClick={() => setRemediationTab('explanation')}
            className={`pb-2 transition-all border-b-2 px-1 flex items-center gap-1.5 ${remediationTab === 'explanation' ? 'border-primary text-primary' : 'border-transparent text-muted-foreground'}`}
          >
            <BookOpen className="h-3.5 w-3.5" />
            <span>Explanation</span>
          </button>
          <button 
            onClick={() => setRemediationTab('remediation')}
            className={`pb-2 transition-all border-b-2 px-1 flex items-center gap-1.5 ${remediationTab === 'remediation' ? 'border-primary text-primary' : 'border-transparent text-muted-foreground'}`}
          >
            <FileText className="h-3.5 w-3.5" />
            <span>Remediation Rules</span>
          </button>
          <button 
            onClick={() => setRemediationTab('code')}
            className={`pb-2 transition-all border-b-2 px-1 flex items-center gap-1.5 ${remediationTab === 'code' ? 'border-primary text-primary' : 'border-transparent text-muted-foreground'}`}
          >
            <Code2 className="h-3.5 w-3.5" />
            <span>Fixed Code (Before/After)</span>
          </button>
          <button 
            onClick={() => setRemediationTab('reference')}
            className={`pb-2 transition-all border-b-2 px-1 flex items-center gap-1.5 ${remediationTab === 'reference' ? 'border-primary text-primary' : 'border-transparent text-muted-foreground'}`}
          >
            <Settings className="h-3.5 w-3.5" />
            <span>References</span>
          </button>
        </div>

        {/* Tab Contents */}
        <div className="text-xs leading-relaxed text-foreground bg-muted/10 p-4 border border-border/50 rounded-xl">
          {remediationTab === 'explanation' && (
            <p className="whitespace-pre-wrap">{explanation}</p>
          )}

          {remediationTab === 'remediation' && (
            <p className="whitespace-pre-wrap">{recommendation}</p>
          )}

          {remediationTab === 'code' && (
            <div className="space-y-4">
              {beforeCode && (
                <div>
                  <h5 className="font-bold text-red-500 mb-1">Insecure Code (Before):</h5>
                  <pre className="p-3 bg-red-500/5 text-slate-100 rounded-lg border border-red-500/10 font-mono text-[11px] overflow-x-auto">
                    <code>{beforeCode}</code>
                  </pre>
                </div>
              )}
              {afterCode && (
                <div>
                  <h5 className="font-bold text-green-500 mb-1">Secure Correction (After):</h5>
                  <pre className="p-3 bg-green-500/5 text-slate-100 rounded-lg border border-green-500/10 font-mono text-[11px] overflow-x-auto">
                    <code>{afterCode}</code>
                  </pre>
                </div>
              )}
              {!beforeCode && !afterCode && (
                <p>Standard fixes are described in the remediation rules text block.</p>
              )}
            </div>
          )}

          {remediationTab === 'reference' && (
            <div className="font-medium">
              <span className="text-muted-foreground">Standard classification: </span>
              <span className="text-foreground">{reference}</span>
            </div>
          )}
        </div>
      </div>
    );
  };

  // If no report selected, render listing select dashboard
  if (!reportId) {
    return (
      <div className="space-y-6 animate-fade-in">
        <div>
          <h2 className="text-2xl font-extrabold tracking-tight font-sans text-foreground">
            Analysis Reports Explorer
          </h2>
          <p className="text-sm text-muted-foreground mt-1">
            Choose an audit record from project: <strong>{activeProject?.name}</strong> to inspect code findings.
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Historical Run Audits</CardTitle>
            <CardDescription>Select an evaluation below to launch interactive reviews.</CardDescription>
          </CardHeader>
          <CardContent>
            {listLoading ? (
              <div className="flex h-36 items-center justify-center">
                <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent"></div>
              </div>
            ) : reportsList.length === 0 ? (
              <div className="flex flex-col items-center justify-center text-center py-12">
                <Terminal className="h-12 w-12 text-muted-foreground/60 mb-3" />
                <h3 className="text-sm font-semibold">No audit reports found</h3>
                <p className="text-xs text-muted-foreground mt-1 max-w-xs mb-6">
                  You haven't run any evaluations in this project yet.
                </p>
                <div className="flex items-center gap-3">
                  <Link to="/upload">
                    <Button variant="outline" size="sm">Upload Archive</Button>
                  </Link>
                  <Link to="/paste">
                    <Button size="sm">Paste Snippet</Button>
                  </Link>
                </div>
              </div>
            ) : (
              <div className="divide-y divide-border/40">
                {reportsList.map((rep) => (
                  <div
                    key={rep.id}
                    className="flex items-center justify-between py-4 first:pt-0 last:pb-0 group cursor-pointer"
                    onClick={() => setSearchParams({ report: rep.id })}
                  >
                    <div className="space-y-0.5">
                      <p className="text-sm font-semibold text-foreground group-hover:text-primary transition-colors flex items-center gap-2">
                        <span>Report Scan - {rep.id.substring(0, 8)}</span>
                        <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-bold ${
                          rep.score >= 90 ? 'bg-green-500/10 text-green-500 border border-green-500/20' : 'bg-red-500/10 text-red-500 border border-red-500/20'
                        }`}>
                          Score: {rep.score}/100
                        </span>
                      </p>
                      <p className="text-xs text-muted-foreground truncate max-w-md">
                        {rep.summary.substring(0, 100)}...
                      </p>
                      <p className="text-[10px] text-muted-foreground">
                        Audited: {new Date(rep.created_at).toLocaleString()}
                      </p>
                    </div>
                    <ChevronRight className="h-5 w-5 text-muted-foreground group-hover:text-foreground group-hover:translate-x-1 transition-all" />
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    );
  }

  // If report ID is selected, show details review workspace split panel
  return (
    <div className="space-y-6 animate-fade-in relative min-h-[85vh]">
      
      {/* Back header navigation button */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <button
          onClick={() => setSearchParams({})}
          className="inline-flex items-center gap-2 text-xs font-semibold text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>Back to reports list</span>
        </button>

        {report && (
          <div className="flex items-center gap-3">
            
            {/* Share link button */}
            <div className="relative">
              <Button
                variant="outline"
                size="sm"
                onClick={handleShareReport}
                className="flex items-center gap-1.5"
              >
                <Share2 className="h-4 w-4" />
                <span>{shareSuccess ? 'Copied!' : 'Share'}</span>
              </Button>
            </div>

            {/* Download selector dropdown */}
            <div className="relative">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setDownloadDropdown(!downloadDropdown)}
                className="flex items-center gap-1.5"
              >
                <Download className="h-4 w-4" />
                <span>Download Report</span>
              </Button>
              {downloadDropdown && (
                <div className="absolute right-0 mt-2 w-36 bg-card border border-border shadow-xl rounded-lg z-50 py-1 text-xs">
                  <button
                    onClick={() => handleDownloadExport('JSON')}
                    className="w-full text-left px-4 py-2 hover:bg-muted font-medium text-foreground transition-colors"
                  >
                    JSON Format
                  </button>
                  <button
                    onClick={() => handleDownloadExport('CSV')}
                    className="w-full text-left px-4 py-2 hover:bg-muted font-medium text-foreground transition-colors"
                  >
                    CSV Format
                  </button>
                </div>
              )}
            </div>

            <span className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-bold border ${
              report.score >= 90 
                ? 'bg-green-500/10 text-green-500 border-green-500/20' 
                : report.score >= 75 
                ? 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20' 
                : 'bg-red-500/10 text-red-500 border-red-500/20'
            }`}>
              Project Security Score: {report.score}/100
            </span>
          </div>
        )}
      </div>

      {loading ? (
        <div className="flex h-[60vh] w-full items-center justify-center">
          <div className="flex flex-col items-center gap-3">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent"></div>
            <p className="text-sm text-muted-foreground animate-pulse">Decompiling and analyzing source trees...</p>
          </div>
        </div>
      ) : !report ? (
        <Card className="p-8 text-center border-dashed border-destructive/20">
          <AlertTriangle className="h-12 w-12 text-destructive mx-auto mb-3" />
          <h3 className="text-lg font-bold text-destructive">Report Fetch Error</h3>
          <p className="text-sm text-muted-foreground mt-2">
            Failed to retrieve details for report query: <strong>{reportId}</strong>. Confirm validation keys.
          </p>
        </Card>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start pb-20">
          
          {/* LEFT PANEL: Vulnerabilities Findings List */}
          <div className="lg:col-span-5 space-y-4 max-h-[80vh] overflow-y-auto pr-2">
            <h3 className="text-sm font-bold text-muted-foreground uppercase tracking-wider mb-2">
              Detected Vulnerabilities ({report.findings.length})
            </h3>
            
            {report.findings.length === 0 ? (
              <Card className="p-6 text-center border-dashed border-green-500/20 bg-green-500/5">
                <CheckCircle className="h-10 w-10 text-green-500 mx-auto mb-2" />
                <h4 className="font-bold text-green-500">Security Clearance Passed</h4>
                <p className="text-xs text-muted-foreground mt-1">
                  Static analysis did not identify any critical threats inside active submissions.
                </p>
              </Card>
            ) : (
              report.findings.map((find) => (
                <div
                  key={find.id}
                  onClick={() => setSelectedFinding(find)}
                  className={`p-4 rounded-xl border cursor-pointer transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md ${
                    selectedFinding?.id === find.id
                      ? 'border-primary bg-primary/5 shadow-sm'
                      : 'border-border bg-card'
                  }`}
                >
                  <div className="flex items-start justify-between gap-3 mb-2">
                    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-bold border ${severityColors[find.severity] || ''}`}>
                      {find.severity}
                    </span>
                    <span className="text-[10px] uppercase font-bold text-muted-foreground tracking-wider">
                      {find.category}
                    </span>
                  </div>
                  <h4 className="text-sm font-bold text-foreground truncate">{find.title}</h4>
                  <p className="text-xs text-muted-foreground truncate mt-1">
                    {find.file_path}:L{find.line_number}
                  </p>
                </div>
              ))
            )}
          </div>

          {/* RIGHT PANEL: Code Viewer & Remediation Instructions */}
          <div className="lg:col-span-7 space-y-6">
            {selectedFinding ? (
              <div className="space-y-6">
                
                {/* Findings Details Card */}
                <Card>
                  <CardHeader>
                    <div className="flex items-center justify-between mb-2">
                      <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-bold border ${severityColors[selectedFinding.severity] || ''}`}>
                        {selectedFinding.severity}
                      </span>
                      <span className="text-xs uppercase font-bold text-muted-foreground tracking-widest">
                        {selectedFinding.category} Category
                      </span>
                    </div>
                    <CardTitle className="text-xl font-extrabold">{selectedFinding.title}</CardTitle>
                    <CardDescription className="text-xs">
                      Located in: <span className="font-mono text-foreground font-semibold">{selectedFinding.file_path}</span> at line: <span className="font-mono font-semibold text-primary">{selectedFinding.line_number}</span>
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    
                    {/* Vulnerability Description */}
                    <div>
                      <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-1">Description</h4>
                      <p className="text-sm leading-relaxed text-foreground/95 bg-muted/20 p-3 rounded-lg border border-border/50 whitespace-pre-line">
                        {selectedFinding.description}
                      </p>
                    </div>

                    {/* Highlighted Code Snippet */}
                    {selectedFinding.code_snippet && (
                      <div>
                        <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-1.5 flex items-center gap-1.5">
                          <FileCode className="h-3.5 w-3.5" />
                          <span>Code snippet</span>
                        </h4>
                        <div className="rounded-lg overflow-hidden border border-border">
                          <div className="bg-muted px-4 py-1.5 flex items-center justify-between border-b border-border text-[10px] text-muted-foreground font-mono">
                            <span>{selectedFinding.file_path.split('/').pop()}</span>
                            <span>Line {selectedFinding.line_number}</span>
                          </div>
                          <pre className="p-4 bg-[#0a0f1d] text-slate-100 text-xs font-mono overflow-x-auto select-all leading-relaxed">
                            <code>
                              <span className="text-muted-foreground mr-3 select-none">{selectedFinding.line_number} |</span>
                              {selectedFinding.code_snippet}
                            </code>
                          </pre>
                        </div>
                      </div>
                    )}

                    {/* Interactive Tabbed Remediation Section */}
                    {selectedFinding.recommendation && (
                      <div>
                        <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-1.5">Remediation Guide</h4>
                        {renderRemediationTabs(selectedFinding.recommendation)}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>
            ) : (
              <Card className="h-96 flex flex-col items-center justify-center text-center p-8 border-dashed">
                <HelpCircle className="h-12 w-12 text-muted-foreground/60 mb-2" />
                <p className="text-sm font-semibold">No vulnerability selected</p>
                <p className="text-xs text-muted-foreground mt-1 max-w-xs">
                  Click on an audit finding on the left navigation panel to load code snippets and corrective recommendations.
                </p>
              </Card>
            )}
          </div>
        </div>
      )}

      {/* FLOATING CONVERSATIONAL CODE ASSISTANT WIDGET */}
      <div className="fixed bottom-6 right-6 z-50">
        {!chatOpen ? (
          <button
            onClick={() => setChatOpen(true)}
            className="flex items-center gap-2 px-4 py-3 bg-primary text-primary-foreground hover:bg-primary/90 shadow-xl hover:shadow-2xl active:scale-95 transition-all rounded-full font-bold text-xs"
          >
            <MessageSquare className="h-4.5 w-4.5" />
            <span>Chat Assistant</span>
          </button>
        ) : (
          <div className="w-80 md:w-[420px] h-[550px] bg-card border border-border/80 shadow-2xl rounded-2xl flex flex-col overflow-hidden animate-slide-up">
            
            <div className="bg-primary px-4 py-3 text-primary-foreground flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Bot className="h-4.5 w-4.5" />
                <span className="text-xs font-extrabold font-sans">Conversational Code Assistant</span>
              </div>
              <button
                onClick={() => setChatOpen(false)}
                className="text-primary-foreground/80 hover:text-primary-foreground transition-colors"
              >
                <X className="h-4.5 w-4.5" />
              </button>
            </div>

            <div className="flex-1 p-4 overflow-y-auto space-y-4 bg-muted/10">
              {chatMessages.map((msg, idx) => (
                <div
                  key={idx}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[85%] rounded-xl px-3 py-2 text-xs leading-relaxed ${
                      msg.role === 'user'
                        ? 'bg-primary text-primary-foreground font-semibold rounded-tr-none'
                        : 'bg-card border border-border/50 text-foreground rounded-tl-none whitespace-pre-line'
                    }`}
                  >
                    {msg.content}
                  </div>
                </div>
              ))}
              {chatLoading && (
                <div className="flex justify-start">
                  <div className="bg-card border border-border/50 rounded-xl px-3 py-2 flex items-center gap-1.5">
                    <span className="h-2 w-2 bg-muted-foreground/60 animate-bounce rounded-full"></span>
                    <span className="h-2 w-2 bg-muted-foreground/60 animate-bounce delay-75 rounded-full"></span>
                    <span className="h-2 w-2 bg-muted-foreground/60 animate-bounce delay-150 rounded-full"></span>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            <form onSubmit={handleSendChat} className="p-3 border-t border-border bg-card flex gap-2">
              <input
                type="text"
                placeholder="Ask about guidelines or quality fixes..."
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                disabled={chatLoading}
                className="flex-1 bg-muted/30 border border-border/60 rounded-lg px-3 py-1.5 text-xs text-foreground focus:outline-none focus:border-primary/80"
              />
              <button
                type="submit"
                disabled={chatLoading || !chatInput.trim()}
                className="p-1.5 bg-primary text-primary-foreground hover:bg-primary/95 rounded-lg active:scale-95 disabled:opacity-40 transition-all"
              >
                <Send className="h-4.5 w-4.5" />
              </button>
            </form>
          </div>
        )}
      </div>

    </div>
  );
};

export default ReviewResults;
