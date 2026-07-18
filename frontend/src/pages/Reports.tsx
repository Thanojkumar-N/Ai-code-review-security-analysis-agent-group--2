import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import apiClient from '../api/client';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import Button from '../components/ui/Button';
import Select from '../components/ui/Select';
import { 
  BarChart4, 
  Download, 
  FileText, 
  FileJson, 
  Table, 
  CheckCircle,
  AlertTriangle 
} from 'lucide-react';

interface Report {
  id: string;
  summary: string;
  score: number;
  created_at: string;
}

export const Reports: React.FC = () => {
  const { activeProject } = useAuth();
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(false);
  const [exportingId, setExportingId] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    const fetchReports = async () => {
      if (!activeProject) return;
      setLoading(true);
      try {
        const response = await apiClient.get<Report[]>(`/reports/project/${activeProject.id}`);
        setReports(response.data);
      } catch (err) {
        console.error('Failed to load project reports', err);
      } finally {
        setLoading(false);
      }
    };

    fetchReports();
  }, [activeProject]);

  const handleExport = async (reportId: string, format: 'PDF' | 'JSON' | 'CSV') => {
    setExportingId(`${reportId}-${format}`);
    setErrorMsg(null);
    setSuccessMsg(null);
    try {
      const response = await apiClient.post(`/reports/${reportId}/export`, {
        report_id: reportId,
        export_type: format,
      });

      // Show mock success link pointing to local backend file system or download mock
      const path = response.data.file_path;
      setSuccessMsg(`Export file (${format}) created successfully: ${path.split(/[\\/]/).pop()}`);
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to generate report export document.');
    } finally {
      setExportingId(null);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h2 className="text-2xl font-extrabold tracking-tight font-sans text-foreground">
          Report Archives
        </h2>
        <p className="text-sm text-muted-foreground mt-1">
          Export analysis findings and metrics into portable formats (PDF, JSON, CSV).
        </p>
      </div>

      {/* Global Success / Error Banners */}
      {successMsg && (
        <div className="flex items-center gap-3 rounded-lg bg-green-500/10 p-3 border border-green-500/20 text-green-500 text-xs">
          <CheckCircle className="h-4 w-4 flex-shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      {errorMsg && (
        <div className="flex items-center gap-3 rounded-lg bg-destructive/10 p-3 border border-destructive/20 text-destructive text-xs">
          <AlertTriangle className="h-4 w-4 flex-shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Audited Code Reports</CardTitle>
          <CardDescription>
            Download summaries or export raw data tables for integration.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex h-36 items-center justify-center">
              <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent"></div>
            </div>
          ) : reports.length === 0 ? (
            <div className="flex flex-col items-center justify-center text-center py-12">
              <BarChart4 className="h-12 w-12 text-muted-foreground/60 mb-3" />
              <h3 className="text-sm font-semibold">No reports to export</h3>
              <p className="text-xs text-muted-foreground mt-1 max-w-xs">
                Audits must be executed before compiling documentation.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto rounded-lg border border-border">
              <table className="w-full text-left border-collapse text-sm">
                <thead>
                  <tr className="bg-muted/50 border-b border-border/80 text-muted-foreground font-semibold text-xs uppercase tracking-wider">
                    <th className="p-4">Report ID</th>
                    <th className="p-4">Created Date</th>
                    <th className="p-4">Vulnerability Score</th>
                    <th className="p-4 text-right">Compile Export File</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/30">
                  {reports.map((rep) => (
                    <tr key={rep.id} className="hover:bg-muted/10 transition-colors">
                      <td className="p-4 font-mono font-medium text-foreground">
                        {rep.id.substring(0, 8)}...
                      </td>
                      <td className="p-4 text-muted-foreground text-xs">
                        {new Date(rep.created_at).toLocaleString()}
                      </td>
                      <td className="p-4">
                        <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-bold ${
                          rep.score >= 90 
                            ? 'bg-green-500/10 text-green-500 border border-green-500/20' 
                            : rep.score >= 75 
                            ? 'bg-yellow-500/10 text-yellow-500 border border-yellow-500/20' 
                            : 'bg-red-500/10 text-red-500 border border-red-500/20'
                        }`}>
                          Score: {rep.score}/100
                        </span>
                      </td>
                      <td className="p-4 text-right flex justify-end gap-2">
                        
                        <Button
                          variant="outline"
                          size="sm"
                          className="h-8 px-2 py-1.5 flex items-center gap-1 text-[11px]"
                          onClick={() => handleExport(rep.id, 'PDF')}
                          isLoading={exportingId === `${rep.id}-PDF`}
                        >
                          <FileText className="h-3.5 w-3.5" />
                          <span>PDF</span>
                        </Button>

                        <Button
                          variant="outline"
                          size="sm"
                          className="h-8 px-2 py-1.5 flex items-center gap-1 text-[11px]"
                          onClick={() => handleExport(rep.id, 'JSON')}
                          isLoading={exportingId === `${rep.id}-JSON`}
                        >
                          <FileJson className="h-3.5 w-3.5" />
                          <span>JSON</span>
                        </Button>

                        <Button
                          variant="outline"
                          size="sm"
                          className="h-8 px-2 py-1.5 flex items-center gap-1 text-[11px]"
                          onClick={() => handleExport(rep.id, 'CSV')}
                          isLoading={exportingId === `${rep.id}-CSV`}
                        >
                          <Table className="h-3.5 w-3.5" />
                          <span>CSV</span>
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
export default Reports;
