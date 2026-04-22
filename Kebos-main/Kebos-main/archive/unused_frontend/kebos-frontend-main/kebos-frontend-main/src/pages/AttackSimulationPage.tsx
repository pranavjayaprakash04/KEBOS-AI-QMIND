import React, { useState } from "react";
import {
  Shield,
  AlertTriangle,
  Clock,
  Play,
  X,
  CheckCircle,
  XCircle,
  Eye,
  Download,
} from "lucide-react";

interface SimulationTemplate {
  id: string;
  name: string;
  description: string;
  type: "api" | "prompt" | "model" | "data" | "network";
  complexity: "low" | "medium" | "high";
  estimatedDuration: number; // in minutes
  targetSystems: string[];
}

interface SimulationJob {
  id: string;
  templateId: string;
  status: "queued" | "running" | "completed" | "failed";
  progress: number;
  startTime: string;
  endTime?: string;
  results?: SimulationResult;
}

interface SimulationResult {
  success: boolean;
  vulnerabilitiesFound: number;
  details: {
    description: string;
    severity: "low" | "medium" | "high" | "critical";
    mitigationSteps?: string[];
  }[];
  summary: string;
}

const AttackSimulationPage: React.FC = () => {
  const [selectedTemplate, setSelectedTemplate] =
    useState<SimulationTemplate | null>(null);
  const [selectedJob, setSelectedJob] = useState<SimulationJob | null>(null);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [isStarting, setIsStarting] = useState(false);
  const [isCancelling, setIsCancelling] = useState(false);

  // Mock data - templates
  const templates: SimulationTemplate[] = [
    {
      id: "template-1",
      name: "API Vulnerability Scanner",
      description:
        "Scans for common API vulnerabilities including injection, authentication, and authorization flaws.",
      type: "api",
      complexity: "medium",
      estimatedDuration: 15,
      targetSystems: ["API Gateway", "Authentication Service"],
    },
    {
      id: "template-2",
      name: "Prompt Injection Test",
      description:
        "Tests LLM systems for prompt injection vulnerabilities that could lead to data leakage or unauthorized actions.",
      type: "prompt",
      complexity: "high",
      estimatedDuration: 30,
      targetSystems: ["GenAI Assistant", "Chat Interface"],
    },
    {
      id: "template-3",
      name: "Model Extraction Attempt",
      description:
        "Simulates attempts to extract model parameters or training data through carefully crafted inputs.",
      type: "model",
      complexity: "high",
      estimatedDuration: 45,
      targetSystems: ["ML Model API", "Inference Engine"],
    },
    {
      id: "template-4",
      name: "Data Poisoning Simulation",
      description:
        "Tests resilience against training data poisoning attacks that could compromise model integrity.",
      type: "data",
      complexity: "medium",
      estimatedDuration: 20,
      targetSystems: ["Training Pipeline", "Data Validation Service"],
    },
    {
      id: "template-5",
      name: "Network Traffic Analysis",
      description:
        "Analyzes network traffic patterns to identify potential vulnerabilities in communication protocols.",
      type: "network",
      complexity: "low",
      estimatedDuration: 10,
      targetSystems: ["Network Layer", "Communication Channels"],
    },
  ];

  // Mock data - jobs
  const jobs: SimulationJob[] = [
    {
      id: "job-1",
      templateId: "template-2",
      status: "completed",
      progress: 100,
      startTime: new Date(Date.now() - 3600000).toISOString(),
      endTime: new Date(Date.now() - 1800000).toISOString(),
      results: {
        success: true,
        vulnerabilitiesFound: 3,
        details: [
          {
            description:
              "Successful prompt injection allowing system prompt extraction",
            severity: "critical",
            mitigationSteps: [
              "Implement input sanitization for all user inputs",
              "Add prompt injection detection mechanisms",
              "Use a robust prompt engineering framework with security controls",
            ],
          },
          {
            description:
              "Partial model behavior manipulation through crafted inputs",
            severity: "high",
            mitigationSteps: [
              "Implement stricter input validation",
              "Add content filtering for potentially malicious inputs",
              "Monitor model outputs for unexpected behavior",
            ],
          },
          {
            description: "Information disclosure through prompt manipulation",
            severity: "medium",
            mitigationSteps: [
              "Limit information exposure in model responses",
              "Implement proper access controls for sensitive data",
              "Regular security audits of prompt templates",
            ],
          },
        ],
        summary:
          "The simulation identified several vulnerabilities in the prompt handling system. Most critical is the ability to extract system prompts through injection attacks, which could expose sensitive information about system design and capabilities.",
      },
    },
    {
      id: "job-2",
      templateId: "template-4",
      status: "running",
      progress: 65,
      startTime: new Date(Date.now() - 900000).toISOString(),
    },
    {
      id: "job-3",
      templateId: "template-1",
      status: "queued",
      progress: 0,
      startTime: new Date().toISOString(),
    },
  ];

  // Helper functions
  const getTemplateById = (id: string): SimulationTemplate | undefined => {
    return templates.find((template) => template.id === id);
  };

  const formatDuration = (minutes: number): string => {
    if (minutes < 60) {
      return `${minutes} min`;
    }
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;
    return remainingMinutes > 0
      ? `${hours}h ${remainingMinutes}m`
      : `${hours}h`;
  };

  const getStatusColor = (status: SimulationJob["status"]): string => {
    switch (status) {
      case "queued":
        return "bg-slate-100 text-slate-700 border-slate-200";
      case "running":
        return "bg-blue-100 text-blue-700 border-blue-200";
      case "completed":
        return "bg-emerald-100 text-emerald-700 border-emerald-200";
      case "failed":
        return "bg-red-100 text-red-700 border-red-200";
      default:
        return "bg-slate-100 text-slate-700 border-slate-200";
    }
  };

  const getSeverityColor = (severity: string): string => {
    switch (severity) {
      case "low":
        return "bg-blue-100 text-blue-700 border-blue-200";
      case "medium":
        return "bg-amber-100 text-amber-700 border-amber-200";
      case "high":
        return "bg-orange-100 text-orange-700 border-orange-200";
      case "critical":
        return "bg-red-100 text-red-700 border-red-200";
      default:
        return "bg-slate-100 text-slate-700 border-slate-200";
    }
  };

  const getComplexityColor = (
    complexity: SimulationTemplate["complexity"]
  ): string => {
    switch (complexity) {
      case "low":
        return "bg-emerald-100 text-emerald-700 border-emerald-200";
      case "medium":
        return "bg-amber-100 text-amber-700 border-amber-200";
      case "high":
        return "bg-red-100 text-red-700 border-red-200";
      default:
        return "bg-slate-100 text-slate-700 border-slate-200";
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case "api":
        return <Shield className="w-4 h-4" />;
      case "prompt":
        return <AlertTriangle className="w-4 h-4" />;
      case "model":
        return <Eye className="w-4 h-4" />;
      case "data":
        return <Shield className="w-4 h-4" />;
      case "network":
        return <Shield className="w-4 h-4" />;
      default:
        return <Shield className="w-4 h-4" />;
    }
  };

  const formatTime = (isoString: string): string => {
    const date = new Date(isoString);
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  };

  const formatDate = (isoString: string): string => {
    const date = new Date(isoString);
    return date.toLocaleDateString();
  };

  const handleStartSimulation = async () => {
    if (!selectedTemplate) return;
    setIsStarting(true);
    // Simulate API call
    setTimeout(() => {
      setIsStarting(false);
      setShowConfirmModal(false);
      // In real app, would refresh jobs list
    }, 2000);
  };

  const handleCancelSimulation = async (jobId: string) => {
    setIsCancelling(true);
    // Simulate API call for cancelling job with ID: jobId
    console.log(`Cancelling simulation job: ${jobId}`);
    setTimeout(() => {
      setIsCancelling(false);
    }, 1500);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      {/* Header */}
      <div className="bg-white/80 backdrop-blur-sm border-b border-slate-200/50 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg shadow-lg">
                <Shield className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-slate-800 to-slate-600 bg-clip-text text-transparent">
                  Attack Simulation
                </h1>
                <p className="text-slate-600 text-sm">
                  Test your systems against simulated cyber attacks
                </p>
              </div>
            </div>
            <button
              className="px-4 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white font-medium rounded-lg shadow-lg hover:shadow-xl transition-all duration-200 transform hover:scale-105"
              onClick={() => {
                setSelectedTemplate(null);
                setSelectedJob(null);
              }}
            >
              View Dashboard
            </button>
          </div>
        </div>
      </div>

      {/* Confirmation Modal */}
      {showConfirmModal && selectedTemplate && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full transform transition-all duration-200">
            <div className="p-6">
              <div className="flex items-center space-x-3 mb-4">
                <div className="p-2 bg-amber-100 rounded-lg">
                  <AlertTriangle className="w-5 h-5 text-amber-600" />
                </div>
                <h3 className="text-xl font-semibold text-slate-800">
                  Confirm Simulation
                </h3>
              </div>
              <p className="text-slate-600 mb-6">
                Are you sure you want to start the{" "}
                <strong className="text-slate-800">
                  {selectedTemplate.name}
                </strong>{" "}
                simulation? This will simulate attacks on your systems.
              </p>
              <div className="flex justify-end space-x-3">
                <button
                  className="px-4 py-2 border border-slate-300 hover:border-slate-400 rounded-lg text-slate-700 hover:bg-slate-50 transition-all duration-200"
                  onClick={() => setShowConfirmModal(false)}
                  disabled={isStarting}
                >
                  Cancel
                </button>
                <button
                  className="px-4 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white rounded-lg font-medium transition-all duration-200 disabled:opacity-50 flex items-center space-x-2"
                  onClick={handleStartSimulation}
                  disabled={isStarting}
                >
                  {isStarting ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                      <span>Starting...</span>
                    </>
                  ) : (
                    <>
                      <Play className="w-4 h-4" />
                      <span>Start Simulation</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Panel - Templates or Job Details */}
          <div className="lg:col-span-1">
            {selectedJob ? (
              <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/50 p-6">
                <div className="flex justify-between items-start mb-6">
                  <h2 className="text-xl font-semibold text-slate-800">
                    Job Details
                  </h2>
                  <button
                    className="p-2 hover:bg-slate-100 rounded-lg transition-colors duration-200"
                    onClick={() => setSelectedJob(null)}
                  >
                    <X className="w-5 h-5 text-slate-500" />
                  </button>
                </div>

                <div className="mb-4">
                  <span
                    className={`text-xs font-medium px-3 py-1 rounded-full border ${getStatusColor(selectedJob.status)}`}
                  >
                    {selectedJob.status.charAt(0).toUpperCase() +
                      selectedJob.status.slice(1)}
                  </span>
                </div>

                <h3 className="text-lg font-medium mb-2 text-slate-800">
                  {getTemplateById(selectedJob.templateId)?.name ||
                    "Unknown Template"}
                </h3>

                <p className="text-slate-600 mb-6">
                  {getTemplateById(selectedJob.templateId)?.description ||
                    "No description available"}
                </p>

                <div className="mb-6">
                  <div className="flex justify-between mb-2">
                    <span className="text-sm font-medium text-slate-700">
                      Progress
                    </span>
                    <span className="text-sm font-medium text-slate-700">
                      {selectedJob.progress}%
                    </span>
                  </div>
                  <div className="w-full bg-slate-200 rounded-full h-2">
                    <div
                      className="bg-gradient-to-r from-indigo-500 to-purple-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${selectedJob.progress}%` }}
                    ></div>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4 mb-6">
                  <div className="bg-slate-50 rounded-lg p-3">
                    <p className="text-xs text-slate-500 mb-1">Started</p>
                    <p className="font-medium text-slate-800">
                      {formatTime(selectedJob.startTime)}
                    </p>
                    <p className="text-xs text-slate-500">
                      {formatDate(selectedJob.startTime)}
                    </p>
                  </div>
                  {selectedJob.endTime && (
                    <div className="bg-slate-50 rounded-lg p-3">
                      <p className="text-xs text-slate-500 mb-1">Completed</p>
                      <p className="font-medium text-slate-800">
                        {formatTime(selectedJob.endTime)}
                      </p>
                      <p className="text-xs text-slate-500">
                        {formatDate(selectedJob.endTime)}
                      </p>
                    </div>
                  )}
                </div>

                {selectedJob.status === "running" && (
                  <button
                    className="w-full px-4 py-2 bg-red-100 hover:bg-red-200 text-red-700 rounded-lg font-medium transition-colors duration-200 flex items-center justify-center space-x-2"
                    onClick={() => handleCancelSimulation(selectedJob.id)}
                    disabled={isCancelling}
                  >
                    {isCancelling ? (
                      <>
                        <div className="w-4 h-4 border-2 border-red-400/30 border-t-red-600 rounded-full animate-spin"></div>
                        <span>Cancelling...</span>
                      </>
                    ) : (
                      <>
                        <X className="w-4 h-4" />
                        <span>Cancel Simulation</span>
                      </>
                    )}
                  </button>
                )}
              </div>
            ) : (
              <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/50 p-6">
                <h2 className="text-xl font-semibold mb-6 text-slate-800">
                  Simulation Templates
                </h2>

                <div className="space-y-4">
                  {templates.map((template) => (
                    <div
                      key={template.id}
                      className="group border border-slate-200 hover:border-indigo-300 rounded-xl p-4 cursor-pointer transition-all duration-200 hover:shadow-lg hover:bg-white/50"
                      onClick={() => setSelectedTemplate(template)}
                    >
                      <div className="flex justify-between items-start mb-3">
                        <div className="flex items-center space-x-2">
                          <div className="p-2 bg-indigo-100 group-hover:bg-indigo-200 rounded-lg transition-colors duration-200">
                            {getTypeIcon(template.type)}
                          </div>
                          <h3 className="font-medium text-slate-800">
                            {template.name}
                          </h3>
                        </div>
                        <span
                          className={`text-xs px-2 py-1 rounded-full border ${getComplexityColor(template.complexity)}`}
                        >
                          {template.complexity}
                        </span>
                      </div>
                      <p className="text-sm text-slate-600 mb-3">
                        {template.description}
                      </p>
                      <div className="flex justify-between items-center">
                        <span className="text-xs bg-slate-100 text-slate-700 px-2 py-1 rounded-full">
                          {template.type}
                        </span>
                        <div className="flex items-center space-x-1 text-slate-500">
                          <Clock className="w-3 h-3" />
                          <span className="text-xs">
                            {formatDuration(template.estimatedDuration)}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Right Panel - Template Details or Results */}
          <div className="lg:col-span-2">
            {selectedTemplate ? (
              <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/50 p-6">
                <div className="flex justify-between items-start mb-6">
                  <div className="flex items-center space-x-3">
                    <div className="p-3 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl shadow-lg">
                      {getTypeIcon(selectedTemplate.type)}
                      <span className="sr-only">Template icon</span>
                    </div>
                    <div>
                      <h2 className="text-2xl font-semibold text-slate-800">
                        {selectedTemplate.name}
                      </h2>
                      <p className="text-slate-600">
                        {selectedTemplate.description}
                      </p>
                    </div>
                  </div>
                  <button
                    className="p-2 hover:bg-slate-100 rounded-lg transition-colors duration-200"
                    onClick={() => setSelectedTemplate(null)}
                  >
                    <X className="w-5 h-5 text-slate-500" />
                  </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                  <div className="bg-gradient-to-br from-blue-50 to-indigo-50 p-4 rounded-xl border border-blue-100">
                    <p className="text-sm text-slate-600 mb-1">Type</p>
                    <p className="font-semibold text-slate-800 capitalize">
                      {selectedTemplate.type}
                    </p>
                  </div>
                  <div className="bg-gradient-to-br from-purple-50 to-pink-50 p-4 rounded-xl border border-purple-100">
                    <p className="text-sm text-slate-600 mb-1">Complexity</p>
                    <p className="font-semibold text-slate-800 capitalize">
                      {selectedTemplate.complexity}
                    </p>
                  </div>
                  <div className="bg-gradient-to-br from-emerald-50 to-teal-50 p-4 rounded-xl border border-emerald-100">
                    <p className="text-sm text-slate-600 mb-1">Duration</p>
                    <p className="font-semibold text-slate-800">
                      {formatDuration(selectedTemplate.estimatedDuration)}
                    </p>
                  </div>
                </div>

                <div className="mb-6">
                  <h3 className="text-lg font-semibold mb-3 text-slate-800">
                    Target Systems
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {selectedTemplate.targetSystems.map((system, index) => (
                      <span
                        key={index}
                        className="bg-indigo-100 text-indigo-700 px-3 py-1 rounded-full text-sm border border-indigo-200"
                      >
                        {system}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="mb-8">
                  <h3 className="text-lg font-semibold mb-3 text-slate-800">
                    Simulation Overview
                  </h3>
                  <div className="bg-gradient-to-br from-slate-50 to-blue-50 p-6 rounded-xl border border-slate-200">
                    {selectedTemplate.type === "api" && (
                      <p className="text-slate-700 leading-relaxed">
                        This simulation tests your API endpoints for common
                        vulnerabilities such as SQL injection, cross-site
                        scripting (XSS), broken authentication, and insecure
                        direct object references. It will attempt to bypass
                        security controls and gain unauthorized access to
                        protected resources.
                      </p>
                    )}
                    {selectedTemplate.type === "prompt" && (
                      <p className="text-slate-700 leading-relaxed">
                        This simulation tests your LLM systems for prompt
                        injection vulnerabilities by sending carefully crafted
                        inputs designed to manipulate the model's behavior,
                        extract sensitive information, or bypass content
                        filters. It evaluates the robustness of your prompt
                        engineering and security controls.
                      </p>
                    )}
                    {selectedTemplate.type === "model" && (
                      <p className="text-slate-700 leading-relaxed">
                        This simulation attempts to extract information about
                        your model architecture, parameters, or training data
                        through a series of targeted queries. It evaluates the
                        risk of model extraction attacks and tests the
                        effectiveness of your model protection mechanisms.
                      </p>
                    )}
                    {selectedTemplate.type === "data" && (
                      <p className="text-slate-700 leading-relaxed">
                        This simulation tests your system's resilience against
                        data poisoning attacks by introducing manipulated inputs
                        into the training pipeline. It evaluates the
                        effectiveness of your data validation controls and the
                        impact of poisoned data on model performance and
                        security.
                      </p>
                    )}
                    {selectedTemplate.type === "network" && (
                      <p className="text-slate-700 leading-relaxed">
                        This simulation analyzes network traffic patterns and
                        communication protocols for potential vulnerabilities.
                        It tests for insecure data transmission, weak
                        encryption, and other network-level security issues that
                        could compromise your AI systems.
                      </p>
                    )}
                  </div>
                </div>

                <div className="flex justify-end">
                  <button
                    className="px-6 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white rounded-lg font-medium shadow-lg hover:shadow-xl transition-all duration-200 transform hover:scale-105 flex items-center space-x-2"
                    onClick={() => setShowConfirmModal(true)}
                  >
                    <Play className="w-4 h-4" />
                    <span>Start Simulation</span>
                  </button>
                </div>
              </div>
            ) : selectedJob && selectedJob.results ? (
              <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/50 p-6">
                <h2 className="text-2xl font-semibold mb-6 text-slate-800">
                  Simulation Results
                </h2>

                <div className="mb-8">
                  <div className="flex items-center mb-6">
                    <div
                      className={`p-4 rounded-2xl mr-4 ${selectedJob.results.success ? "bg-emerald-100" : "bg-red-100"}`}
                    >
                      {selectedJob.results.success ? (
                        <CheckCircle className="w-8 h-8 text-emerald-600" />
                      ) : (
                        <XCircle className="w-8 h-8 text-red-600" />
                      )}
                    </div>
                    <div>
                      <h3 className="text-2xl font-semibold text-slate-800">
                        {selectedJob.results.vulnerabilitiesFound} Vulnerabilit
                        {selectedJob.results.vulnerabilitiesFound === 1
                          ? "y"
                          : "ies"}{" "}
                        Found
                      </h3>
                      <p className="text-slate-600">
                        {selectedJob.results.success
                          ? "Simulation completed successfully"
                          : "Simulation encountered issues"}
                      </p>
                    </div>
                  </div>

                  <div className="bg-gradient-to-br from-blue-50 to-indigo-50 p-6 rounded-xl border border-blue-100 mb-8">
                    <h4 className="font-semibold mb-3 text-slate-800 flex items-center space-x-2">
                      <Eye className="w-4 h-4" />
                      <span>Executive Summary</span>
                    </h4>
                    <p className="text-slate-700 leading-relaxed">
                      {selectedJob.results.summary}
                    </p>
                  </div>
                </div>

                <h3 className="text-xl font-semibold mb-4 text-slate-800">
                  Detailed Findings
                </h3>
                <div className="space-y-4 mb-8">
                  {selectedJob.results.details.map((detail, index) => (
                    <div
                      key={index}
                      className="border border-slate-200 rounded-xl p-6 hover:shadow-lg transition-shadow duration-200"
                    >
                      <div className="flex justify-between items-start mb-4">
                        <h4 className="font-semibold text-slate-800 flex-1 pr-4">
                          {detail.description}
                        </h4>
                        <span
                          className={`text-xs px-3 py-1 rounded-full border font-medium ${getSeverityColor(detail.severity)}`}
                        >
                          {detail.severity.toUpperCase()}
                        </span>
                      </div>
                      {detail.mitigationSteps &&
                        detail.mitigationSteps.length > 0 && (
                          <div className="bg-slate-50 rounded-lg p-4">
                            <h5 className="text-sm font-semibold mb-3 text-slate-700">
                              Recommended Mitigations:
                            </h5>
                            <ul className="space-y-2">
                              {detail.mitigationSteps.map((step, stepIndex) => (
                                <li
                                  key={stepIndex}
                                  className="flex items-start space-x-2"
                                >
                                  <div className="w-1.5 h-1.5 bg-indigo-400 rounded-full mt-2 flex-shrink-0"></div>
                                  <span className="text-sm text-slate-700">
                                    {step}
                                  </span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                    </div>
                  ))}
                </div>

                <div className="flex justify-end space-x-3">
                  <button className="px-4 py-2 border border-slate-300 hover:border-slate-400 rounded-lg text-slate-700 hover:bg-black hover:text-white hover:-translate-y-1 transition-transform  duration-200 flex items-center space-x-2">
                    <Download className="w-4 h-4" />
                    <span>Export Report</span>
                  </button>
                </div>
              </div>
            ) : (
              <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/50 p-6">
                <h2 className="text-2xl font-semibold mb-6 text-slate-800">
                  Active Simulation Jobs
                </h2>

                {jobs && jobs.length > 0 ? (
                  <div className="space-y-4">
                    {jobs.map((job) => (
                      <div
                        key={job.id}
                        className="group border border-slate-200 hover:border-indigo-300 rounded-xl p-4 cursor-pointer transition-all duration-200 hover:shadow-lg hover:bg-white/50"
                        onClick={() => setSelectedJob(job)}
                      >
                        <div className="flex justify-between items-start mb-3">
                          <div className="flex items-center space-x-3">
                            <div className="p-2 bg-indigo-100 group-hover:bg-indigo-200 rounded-lg transition-colors duration-200">
                              {getTypeIcon(
                                getTemplateById(job.templateId)?.type || "api"
                              )}
                            </div>
                            <h3 className="font-semibold text-slate-800">
                              {getTemplateById(job.templateId)?.name ||
                                "Unknown Template"}
                            </h3>
                          </div>
                          <span
                            className={`text-xs px-3 py-1 rounded-full border font-medium ${getStatusColor(job.status)}`}
                          >
                            {job.status.toUpperCase()}
                          </span>
                        </div>

                        {job.status === "running" && (
                          <div className="mb-4">
                            <div className="flex justify-between mb-2">
                              <span className="text-xs text-slate-600 font-medium">
                                Progress
                              </span>
                              <span className="text-xs text-slate-600 font-medium">
                                {job.progress}%
                              </span>
                            </div>
                            <div className="w-full bg-slate-200 rounded-full h-2">
                              <div
                                className="bg-gradient-to-r from-indigo-500 to-purple-600 h-2 rounded-full transition-all duration-300"
                                style={{ width: `${job.progress}%` }}
                              ></div>
                            </div>
                          </div>
                        )}

                        <div className="flex justify-between items-center">
                          <span className="text-xs bg-slate-100 text-slate-700 px-2 py-1 rounded-full">
                            {getTemplateById(job.templateId)?.type || "unknown"}
                          </span>
                          <div className="flex items-center space-x-1 text-slate-500">
                            <Clock className="w-3 h-3" />
                            <span className="text-xs">
                              Started: {formatTime(job.startTime)}
                            </span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <div className="p-4 bg-slate-100 rounded-2xl w-16 h-16 mx-auto mb-4 flex items-center justify-center">
                      <Shield className="w-8 h-8 text-slate-400" />
                    </div>
                    <p className="text-lg text-slate-600 font-medium mb-2">
                      No active simulation jobs
                    </p>
                    <p className="text-sm text-slate-500">
                      Select a template to start a new simulation
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AttackSimulationPage;
