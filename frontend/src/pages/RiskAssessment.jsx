import React, { useState, useEffect, useRef } from 'react';
import {
  ShieldPlus,
  Activity,
  AlertCircle,
  CheckCircle2,
  Database,
  Search,
  Sparkles,
  ChevronDown,
  ChevronUp,
  RotateCcw,
  Layers,
  HelpCircle,
  Download
} from 'lucide-react';
import Sidebar from '../components/Sidebar';
import Header from '../components/Header';
import RiskScoreGauge from '../components/RiskScoreGauge';
import RiskBadge from '../components/RiskBadge';
import RiskFactorsList from '../components/RiskFactorsList';
import MaintenanceBox from '../components/MaintenanceBox';
import RiskComparisonChart from '../charts/RiskComparisonChart';
import RiskTrendTimeline from '../components/RiskTrendTimeline';
import { metadataApi, predictionApi } from '../services/api';

const RiskAssessment = () => {
  // Dropdown Metadata State
  const [options, setOptions] = useState({
    device_categories: [],
    countries: [],
  });

  // 4 Primary User Form Fields (Starts completely empty as required)
  const [primaryForm, setPrimaryForm] = useState({
    name_device: '',
    classification: '',
    implanted: '',
    name_manufacturer: '',
  });

  // Optional Additional Fields (for collapsible accordion)
  const [additionalForm, setAdditionalForm] = useState({
    country_event: '',
    country_device: '',
    quantity_in_commerce: '',
    event_year: '',
    event_month: '',
  });

  // Derived Historical Information from MySQL (Read-Only)
  const [derivedInfo, setDerivedInfo] = useState({
    event_count: null,
    manufacturer_event_count: null,
    avg_quantity_in_commerce: null,
    loaded: false,
    note: '',
  });

  // Manufacturer Server-Side Autocomplete
  const [mfrSearch, setMfrSearch] = useState('');
  const [mfrSuggestions, setMfrSuggestions] = useState([]);
  const [isSearchingMfr, setIsSearchingMfr] = useState(false);
  const [showMfrDropdown, setShowMfrDropdown] = useState(false);
  const mfrWrapperRef = useRef(null);

  // Device Name Server-Side Autocomplete
  const [deviceSearch, setDeviceSearch] = useState('');
  const [deviceSuggestions, setDeviceSuggestions] = useState([]);
  const [isSearchingDevice, setIsSearchingDevice] = useState(false);
  const [showDeviceDropdown, setShowDeviceDropdown] = useState(false);
  const deviceWrapperRef = useRef(null);

  // UI Accordion States
  const [showAdditional, setShowAdditional] = useState(false);
  const [showModelFeatures, setShowModelFeatures] = useState(false);

  // Submission & Validation States
  const [validationError, setValidationError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [assessmentResult, setAssessmentResult] = useState(null);
  // Device Name isn't part of the model / prediction response, so it's captured
  // separately at submission time purely for display in the result & PDF report.
  const [assessedDeviceName, setAssessedDeviceName] = useState('');
  // The exact Device record id, captured only when the user picks a suggestion from
  // the search dropdown (not on free-typed text) so the Risk Trend Timeline always
  // reflects one specific, unambiguous device's real historical event data.
  const [selectedDeviceId, setSelectedDeviceId] = useState(null);
  const [assessedDeviceId, setAssessedDeviceId] = useState(null);

  // Initial Metadata Load
  useEffect(() => {
    const fetchMetadata = async () => {
      try {
        const [categoriesRes, countryRes] = await Promise.all([
          metadataApi.getDeviceCategories(),
          metadataApi.getCountries(),
        ]);
        setOptions({
          device_categories: categoriesRes.data || [],
          countries: countryRes.data || [],
        });
      } catch (err) {
        console.warn('Metadata load error:', err);
      }
    };
    fetchMetadata();
  }, []);

  // Debounced Server-Side Manufacturer Search
  useEffect(() => {
    if (!mfrSearch.trim() || mfrSearch.length < 2) {
      setMfrSuggestions([]);
      return;
    }

    const timer = setTimeout(async () => {
      setIsSearchingMfr(true);
      try {
        const res = await metadataApi.searchManufacturers(mfrSearch.trim(), 1, 20);
        setMfrSuggestions(res.data.items || []);
        setShowMfrDropdown(true);
      } catch (err) {
        console.warn('Manufacturer search error:', err);
      } finally {
        setIsSearchingMfr(false);
      }
    }, 250);

    return () => clearTimeout(timer);
  }, [mfrSearch]);

  // Debounced Server-Side Device Name Search
  useEffect(() => {
    if (!deviceSearch.trim() || deviceSearch.length < 2) {
      setDeviceSuggestions([]);
      return;
    }

    const timer = setTimeout(async () => {
      setIsSearchingDevice(true);
      try {
        const res = await metadataApi.searchDevices(deviceSearch.trim(), 1, 20);
        setDeviceSuggestions(res.data.items || []);
        setShowDeviceDropdown(true);
      } catch (err) {
        console.warn('Device search error:', err);
      } finally {
        setIsSearchingDevice(false);
      }
    }, 250);

    return () => clearTimeout(timer);
  }, [deviceSearch]);

  // Click outside to close manufacturer / device suggestion dropdowns
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (mfrWrapperRef.current && !mfrWrapperRef.current.contains(event.target)) {
        setShowMfrDropdown(false);
      }
      if (deviceWrapperRef.current && !deviceWrapperRef.current.contains(event.target)) {
        setShowDeviceDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Fetch Live Historical Counts from MySQL when Manufacturer or Device Category changes
  useEffect(() => {
    const fetchCounts = async () => {
      if (!primaryForm.name_manufacturer) {
        setDerivedInfo({
          event_count: null,
          manufacturer_event_count: null,
          avg_quantity_in_commerce: null,
          loaded: false,
          note: '',
        });
        return;
      }

      try {
        const res = await metadataApi.getHistoricalCounts({
          manufacturer: primaryForm.name_manufacturer,
          classification: primaryForm.classification || undefined,
        });
        const data = res.data;
        setDerivedInfo({
          event_count: data.event_count,
          manufacturer_event_count: data.manufacturer_event_count,
          avg_quantity_in_commerce: data.avg_quantity_in_commerce > 0 ? data.avg_quantity_in_commerce : null,
          loaded: true,
          note: data.note,
        });
      } catch (err) {
        console.warn('Historical counts lookup error:', err);
      }
    };

    fetchCounts();
  }, [primaryForm.name_manufacturer, primaryForm.classification]);

  const handleDownloadReport = () => {
    window.print();
  };

  const handlePrimaryChange = (e) => {
    const { name, value } = e.target;
    setPrimaryForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleAdditionalChange = (e) => {
    const { name, value } = e.target;
    setAdditionalForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSelectManufacturer = (mfrName) => {
    setPrimaryForm((prev) => ({ ...prev, name_manufacturer: mfrName }));
    setMfrSearch(mfrName);
    setShowMfrDropdown(false);
  };

  const handleSelectDevice = (device) => {
    setPrimaryForm((prev) => ({
      ...prev,
      name_device: device.name,
      // Pre-fill Device Category from the matched device record if not already chosen
      classification: prev.classification || device.classification || '',
    }));
    setSelectedDeviceId(device.id);
    setDeviceSearch(device.name);
    setShowDeviceDropdown(false);
  };

  const handleResetForm = () => {
    setPrimaryForm({
      name_device: '',
      classification: '',
      implanted: '',
      name_manufacturer: '',
    });
    setAdditionalForm({
      country_event: '',
      country_device: '',
      quantity_in_commerce: '',
      event_year: '',
      event_month: '',
    });
    setMfrSearch('');
    setDeviceSearch('');
    setDeviceSuggestions([]);
    setSelectedDeviceId(null);
    setAssessedDeviceName('');
    setAssessedDeviceId(null);
    setDerivedInfo({
      event_count: null,
      manufacturer_event_count: null,
      avg_quantity_in_commerce: null,
      loaded: false,
      note: '',
    });
    setAssessmentResult(null);
    setValidationError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setValidationError('');

    // Strict validation of the 4 Primary Fields
    if (!primaryForm.name_device.trim()) {
      setValidationError('Please enter or search for a Device Name.');
      return;
    }
    if (!primaryForm.classification) {
      setValidationError('Please select the Device Category.');
      return;
    }
    if (!primaryForm.name_manufacturer.trim()) {
      setValidationError('Please enter or search for a Manufacturer Name.');
      return;
    }
    if (!primaryForm.implanted) {
      setValidationError('Please select the Implant Status.');
      return;
    }

    setIsSubmitting(true);
    try {
      const payload = {
        name_device: primaryForm.name_device.trim(),
        classification: primaryForm.classification,
        implanted: primaryForm.implanted,
        name_manufacturer: primaryForm.name_manufacturer.trim(),
      };

      // Optional Additional Fields (if supplied by user)
      if (additionalForm.country_event) payload.country_event = additionalForm.country_event;
      if (additionalForm.country_device) payload.country_device = additionalForm.country_device;
      if (additionalForm.quantity_in_commerce !== '') {
        payload.quantity_in_commerce = parseFloat(additionalForm.quantity_in_commerce);
      }
      if (additionalForm.event_year !== '') {
        payload.event_year = parseInt(additionalForm.event_year, 10);
      }
      if (additionalForm.event_month !== '') {
        payload.event_month = parseInt(additionalForm.event_month, 10);
      }

      const res = await predictionApi.create(payload);
      setAssessedDeviceName(primaryForm.name_device.trim());
      setAssessedDeviceId(selectedDeviceId);
      setAssessmentResult(res.data);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (err) {
      if (err.response && err.response.data && err.response.data.detail) {
        setValidationError(err.response.data.detail);
      } else {
        setValidationError('Assessment request failed. Please check your inputs and try again.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="app-container">
      <Sidebar />

      <div className="main-content">
        <Header
          title="Medical Device Risk Assessment"
          subtitle="Enter the key device and regulatory information to estimate medical device risk."
        />

        <div className="page-body">
          {validationError && (
            <div className="alert alert-danger">
              <AlertCircle size={18} />
              <span>{validationError}</span>
            </div>
          )}

          {/* ASSESSMENT RESULT SECTION (Visible ONLY after explicit submission) */}
          {assessmentResult ? (
            <>
            <div className="no-print" style={{ marginBottom: '2.5rem' }}>
              <div style={{
                backgroundColor: '#ffffff',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-md)',
                padding: '2rem',
                boxShadow: 'var(--shadow-sm)',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.5rem', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '1rem' }}>
                  <div>
                    <span style={{ fontSize: '0.75rem', fontWeight: 800, color: 'var(--primary-600)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                      Model Inference Result
                    </span>
                    <h2 style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--text-primary)', marginTop: '0.2rem' }}>
                      Risk Assessment Completed
                    </h2>
                    <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                      Evaluated on: {new Date(assessmentResult.created_at).toLocaleString()}
                    </p>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <div style={{ textAlign: 'right' }}>
                      <span style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.3rem' }}>
                        Predicted Risk Level
                      </span>
                      <RiskBadge riskLevel={assessmentResult.risk_level} size="large" />
                    </div>
                    <button onClick={handleDownloadReport} className="btn btn-secondary" style={{ fontSize: '0.85rem' }}>
                      <Download size={15} />
                      <span>Download Report</span>
                    </button>
                    <button onClick={handleResetForm} className="btn btn-secondary" style={{ fontSize: '0.85rem' }}>
                      <RotateCcw size={15} />
                      <span>New Assessment</span>
                    </button>
                  </div>
                </div>

                {/* Current Model Risk (XGBoost Prediction) */}
                <span style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.5rem' }}>
                  Current Model Risk (XGBoost Prediction)
                </span>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.5rem', marginBottom: '1.5rem' }}>
                  <RiskScoreGauge
                    scorePercentage={assessmentResult.risk_percentage}
                    riskLevel={assessmentResult.risk_level}
                  />
                  <RiskComparisonChart
                    eventCount={assessmentResult.event_count}
                    manufacturerEventCount={assessmentResult.manufacturer_event_count}
                    riskScore={assessmentResult.risk_score}
                  />
                </div>

                {/* Historical Risk Trend — independent, complementary signal to the XGBoost prediction above */}
                <div style={{ marginBottom: '1.75rem' }}>
                  <RiskTrendTimeline deviceId={assessedDeviceId} deviceName={assessedDeviceName} />
                </div>

                {/* SHAP Explanation Narrative */}
                <div style={{
                  backgroundColor: 'var(--bg-app)',
                  padding: '1.25rem 1.5rem',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border-subtle)',
                  marginBottom: '1.75rem',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                    <Sparkles size={18} color="var(--primary-600)" />
                    <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                      Why Was This Risk Predicted?
                    </h4>
                  </div>
                  <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                    {assessmentResult.explanation}
                  </p>
                </div>

                {/* Contributing Risk Factors */}
                <div style={{ marginBottom: '1.75rem' }}>
                  <h4 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.75rem' }}>
                    Contributing Risk Factors (SHAP Model Insights)
                  </h4>
                  <RiskFactorsList factors={assessmentResult.risk_factors} />
                </div>

                {/* Maintenance Recommendation Protocol */}
                <div style={{ marginBottom: '1.75rem' }}>
                  <MaintenanceBox
                    recommendation={assessmentResult.maintenance_recommendation}
                    riskLevel={assessmentResult.risk_level}
                  />
                </div>

                {/* MODEL TRANSPARENCY SECTION: 13 MODEL FEATURES USED WITH PROVENANCE */}
                <div style={{
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-sm)',
                  overflow: 'hidden',
                }}>
                  <button
                    type="button"
                    onClick={() => setShowModelFeatures(!showModelFeatures)}
                    style={{
                      width: '100%',
                      padding: '1rem 1.25rem',
                      backgroundColor: 'var(--bg-app)',
                      border: 'none',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      cursor: 'pointer',
                      fontSize: '0.95rem',
                      fontWeight: 700,
                      color: 'var(--text-primary)',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <Layers size={18} color="var(--primary-600)" />
                      <span>View 13 Model Features Used (Pipeline Transparency)</span>
                    </div>
                    {showModelFeatures ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                  </button>

                  {showModelFeatures && (
                    <div style={{ padding: '1.25rem', backgroundColor: '#ffffff' }}>
                      <p style={{ fontSize: '0.825rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
                        All 13 features consumed by the XGBoost pipeline, displaying their evaluated values and provenance sources:
                      </p>

                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem' }}>
                        {assessmentResult.features_used && assessmentResult.features_used.map((f, idx) => (
                          <div key={idx} style={{
                            padding: '0.75rem 1rem',
                            backgroundColor: 'var(--bg-app)',
                            border: '1px solid var(--border-subtle)',
                            borderRadius: 'var(--radius-sm)',
                          }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '0.2rem' }}>
                              <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)' }}>
                                {idx + 1}. {f.feature_name}
                              </span>
                              <span style={{
                                fontSize: '0.65rem',
                                fontWeight: 700,
                                padding: '0.1rem 0.4rem',
                                borderRadius: '4px',
                                backgroundColor: f.source.includes('MySQL') ? 'var(--teal-50)' : 'var(--primary-50)',
                                color: f.source.includes('MySQL') ? 'var(--teal-700)' : 'var(--primary-700)',
                                border: '1px solid var(--border-subtle)',
                              }}>
                                {f.source}
                              </span>
                            </div>
                            <span style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-primary)', display: 'block', wordBreak: 'break-word' }}>
                              {String(f.value)}
                            </span>
                            <span style={{ fontSize: '0.7rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                              ML Feature: {f.feature}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

              </div>
            </div>

            {/* PRINT-ONLY REGULATORY-STYLE REPORT (hidden on screen, shown only via window.print()) */}
            <div className="print-report">
              <div style={{ marginBottom: '1.5rem', borderBottom: '2px solid #0f172a', paddingBottom: '0.75rem' }}>
                <h1 style={{ fontSize: '1.5rem', margin: 0 }}>Medical Device Risk Assessment Report</h1>
                <p style={{ fontSize: '0.85rem', color: '#334155', marginTop: '0.35rem' }}>
                  Assessment Date: {new Date(assessmentResult.created_at).toLocaleString()} &nbsp;|&nbsp; Report Generated: {new Date().toLocaleString()}
                </p>
              </div>

              <h2 style={{ fontSize: '1.05rem', marginBottom: '0.5rem' }}>Device Information</h2>
              <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: '1.5rem', fontSize: '0.9rem' }}>
                <tbody>
                  <tr>
                    <td style={{ padding: '0.4rem 0', width: '35%', fontWeight: 700, borderBottom: '1px solid #e2e8f0' }}>Device Name</td>
                    <td style={{ padding: '0.4rem 0', borderBottom: '1px solid #e2e8f0' }}>{assessedDeviceName || 'N/A'}</td>
                  </tr>
                  <tr>
                    <td style={{ padding: '0.4rem 0', fontWeight: 700, borderBottom: '1px solid #e2e8f0' }}>Device Category</td>
                    <td style={{ padding: '0.4rem 0', borderBottom: '1px solid #e2e8f0' }}>{assessmentResult.classification}</td>
                  </tr>
                  <tr>
                    <td style={{ padding: '0.4rem 0', fontWeight: 700, borderBottom: '1px solid #e2e8f0' }}>Manufacturer Name</td>
                    <td style={{ padding: '0.4rem 0', borderBottom: '1px solid #e2e8f0' }}>{assessmentResult.name_manufacturer}</td>
                  </tr>
                  <tr>
                    <td style={{ padding: '0.4rem 0', fontWeight: 700 }}>Implant Status</td>
                    <td style={{ padding: '0.4rem 0' }}>{assessmentResult.implanted === 'YES' ? 'Implanted' : 'Non-implanted'}</td>
                  </tr>
                </tbody>
              </table>

              <h2 style={{ fontSize: '1.05rem', marginBottom: '0.5rem' }}>AI Risk Assessment</h2>
              <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: '1.5rem', fontSize: '0.9rem' }}>
                <tbody>
                  <tr>
                    <td style={{ padding: '0.4rem 0', width: '35%', fontWeight: 700, borderBottom: '1px solid #e2e8f0' }}>Predicted Risk Level</td>
                    <td style={{ padding: '0.4rem 0', borderBottom: '1px solid #e2e8f0', fontWeight: 800 }}>{assessmentResult.risk_level} RISK</td>
                  </tr>
                  <tr>
                    <td style={{ padding: '0.4rem 0', fontWeight: 700 }}>Model Risk Score</td>
                    <td style={{ padding: '0.4rem 0', fontWeight: 800 }}>{Number(assessmentResult.risk_percentage).toFixed(2)}%</td>
                  </tr>
                </tbody>
              </table>

              <h2 style={{ fontSize: '1.05rem', marginBottom: '0.5rem' }}>Why Was This Risk Predicted?</h2>
              <p style={{ fontSize: '0.9rem', lineHeight: 1.6, marginBottom: '1.5rem' }}>{assessmentResult.explanation}</p>

              <h2 style={{ fontSize: '1.05rem', marginBottom: '0.5rem' }}>Contributing Risk Factors (SHAP Model Insights)</h2>
              <ul style={{ marginBottom: '1.5rem', paddingLeft: '1.25rem', fontSize: '0.9rem', lineHeight: 1.6 }}>
                {(assessmentResult.risk_factors || []).map((f, idx) => (
                  <li key={idx} style={{ marginBottom: '0.4rem' }}>
                    <strong>{f.feature_name}</strong> ({f.impact.replace('_', ' ')}): {f.description}
                  </li>
                ))}
              </ul>

              <h2 style={{ fontSize: '1.05rem', marginBottom: '0.5rem' }}>Maintenance Recommendation</h2>
              <pre style={{ fontFamily: 'inherit', whiteSpace: 'pre-wrap', fontSize: '0.9rem', lineHeight: 1.6, marginBottom: '1.5rem' }}>
                {assessmentResult.maintenance_recommendation}
              </pre>

              <p style={{ fontSize: '0.75rem', color: '#64748b', borderTop: '1px solid #e2e8f0', paddingTop: '0.75rem' }}>
                Generated by the MedDevice Risk Monitor decision-support platform (XGBoost model, trained on historical FDA medical-device event data).
              </p>
            </div>
            </>
          ) : (
            <div style={{
              backgroundColor: '#ffffff',
              border: '1px dashed var(--border-subtle)',
              borderRadius: 'var(--radius-md)',
              padding: '1.25rem 1.5rem',
              marginBottom: '1.75rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.75rem',
              color: 'var(--text-muted)',
            }}>
              <Activity size={20} color="var(--primary-600)" />
              <span style={{ fontSize: '0.9rem', fontWeight: 500 }}>
                Complete the required information and select <strong>Assess Risk</strong> to generate an assessment.
              </span>
            </div>
          )}

          {/* PRIMARY DEVICE INFORMATION FORM */}
          <form onSubmit={handleSubmit} className="card" style={{ padding: '2rem' }}>
            <div style={{ marginBottom: '2rem' }}>
              <div style={{ marginBottom: '1.25rem', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '0.75rem' }}>
                <h3 style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                  Device Information
                </h3>
                <p style={{ fontSize: '0.825rem', color: 'var(--text-muted)' }}>
                  Enter the key device parameters below:
                </p>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.25rem' }}>
                {/* Field 1: Device Name Search (Server-Side Autocomplete) */}
                <div className="form-group" style={{ position: 'relative' }} ref={deviceWrapperRef}>
                  <label className="form-label">
                    Device Name <span className="required">*</span>
                  </label>
                  <div style={{ position: 'relative' }}>
                    <input
                      type="text"
                      className="form-control"
                      placeholder="Search device name..."
                      value={deviceSearch}
                      onChange={(e) => {
                        setDeviceSearch(e.target.value);
                        setPrimaryForm((prev) => ({ ...prev, name_device: e.target.value }));
                        // Free-typed text may no longer match the previously selected
                        // device record, so drop the id used by the Risk Trend Timeline.
                        setSelectedDeviceId(null);
                      }}
                      onFocus={() => {
                        if (deviceSuggestions.length > 0) setShowDeviceDropdown(true);
                      }}
                      required
                    />
                    <div style={{ position: 'absolute', right: '10px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }}>
                      {isSearchingDevice ? <Activity size={16} className="animate-spin" /> : <Search size={16} />}
                    </div>
                  </div>

                  {/* Autocomplete Suggestions */}
                  {showDeviceDropdown && deviceSuggestions.length > 0 && (
                    <ul style={{
                      position: 'absolute',
                      top: '100%',
                      left: 0,
                      right: 0,
                      backgroundColor: '#ffffff',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: 'var(--radius-sm)',
                      boxShadow: 'var(--shadow-md)',
                      maxHeight: '220px',
                      overflowY: 'auto',
                      zIndex: 30,
                      listStyle: 'none',
                      margin: '4px 0 0 0',
                      padding: '4px 0',
                    }}>
                      {deviceSuggestions.map((item) => (
                        <li
                          key={item.id}
                          onClick={() => handleSelectDevice(item)}
                          style={{
                            padding: '0.5rem 1rem',
                            fontSize: '0.85rem',
                            cursor: 'pointer',
                            transition: 'background 0.15s ease',
                          }}
                          onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = 'var(--primary-50)')}
                          onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
                        >
                          <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{item.name}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>

                {/* Field 2: Device Category */}
                <div className="form-group">
                  <label className="form-label">
                    Device Category <span className="required">*</span>
                  </label>
                  <select
                    className="form-control"
                    name="classification"
                    value={primaryForm.classification}
                    onChange={handlePrimaryChange}
                    required
                  >
                    <option value="">Select device category</option>
                    {options.device_categories.map((c, idx) => (
                      <option key={idx} value={c}>{c}</option>
                    ))}
                  </select>
                </div>

                {/* Field 3: Manufacturer Name Search (Server-Side Autocomplete) */}
                <div className="form-group" style={{ position: 'relative' }} ref={mfrWrapperRef}>
                  <label className="form-label">
                    Manufacturer Name <span className="required">*</span>
                  </label>
                  <div style={{ position: 'relative' }}>
                    <input
                      type="text"
                      className="form-control"
                      placeholder="Search manufacturer..."
                      value={mfrSearch}
                      onChange={(e) => {
                        setMfrSearch(e.target.value);
                        setPrimaryForm((prev) => ({ ...prev, name_manufacturer: e.target.value }));
                      }}
                      onFocus={() => {
                        if (mfrSuggestions.length > 0) setShowMfrDropdown(true);
                      }}
                      required
                    />
                    <div style={{ position: 'absolute', right: '10px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }}>
                      {isSearchingMfr ? <Activity size={16} className="animate-spin" /> : <Search size={16} />}
                    </div>
                  </div>

                  {/* Autocomplete Suggestions */}
                  {showMfrDropdown && mfrSuggestions.length > 0 && (
                    <ul style={{
                      position: 'absolute',
                      top: '100%',
                      left: 0,
                      right: 0,
                      backgroundColor: '#ffffff',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: 'var(--radius-sm)',
                      boxShadow: 'var(--shadow-md)',
                      maxHeight: '220px',
                      overflowY: 'auto',
                      zIndex: 30,
                      listStyle: 'none',
                      margin: '4px 0 0 0',
                      padding: '4px 0',
                    }}>
                      {mfrSuggestions.map((item) => (
                        <li
                          key={item.id}
                          onClick={() => handleSelectManufacturer(item.name)}
                          style={{
                            padding: '0.5rem 1rem',
                            fontSize: '0.85rem',
                            cursor: 'pointer',
                            transition: 'background 0.15s ease',
                          }}
                          onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = 'var(--primary-50)')}
                          onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
                        >
                          <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{item.name}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>

                {/* Field 4: Implant Status */}
                <div className="form-group">
                  <label className="form-label">
                    Implant Status <span className="required">*</span>
                  </label>
                  <select
                    className="form-control"
                    name="implanted"
                    value={primaryForm.implanted}
                    onChange={handlePrimaryChange}
                    required
                  >
                    <option value="">Select implant status</option>
                    <option value="NO">Non-implanted</option>
                    <option value="YES">Implanted</option>
                  </select>
                </div>
              </div>
            </div>

            {/* SECTION 2: HISTORICAL INFORMATION (Read-only live derived box) */}
            <div style={{
              backgroundColor: 'var(--bg-app)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-sm)',
              padding: '1.25rem',
              marginBottom: '2rem',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.35rem' }}>
                <Database size={16} color="var(--primary-600)" />
                <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                  Historical Information
                </h4>
              </div>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
                Historical event and manufacturer statistics will be retrieved automatically from the medical-device database when available.
              </p>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
                <div style={{ backgroundColor: '#ffffff', padding: '0.75rem 1rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                  <span style={{ fontSize: '0.725rem', fontWeight: 600, color: 'var(--text-muted)' }}>Historical Device Events</span>
                  <span style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--text-primary)', display: 'block', marginTop: '2px' }}>
                    {assessmentResult
                      ? assessmentResult.event_count
                      : (derivedInfo.event_count !== null ? derivedInfo.event_count : 'Automatically calculated')}
                  </span>
                </div>

                <div style={{ backgroundColor: '#ffffff', padding: '0.75rem 1rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                  <span style={{ fontSize: '0.725rem', fontWeight: 600, color: 'var(--text-muted)' }}>Manufacturer Historical Events</span>
                  <span style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--text-primary)', display: 'block', marginTop: '2px' }}>
                    {assessmentResult
                      ? assessmentResult.manufacturer_event_count
                      : (derivedInfo.manufacturer_event_count !== null ? derivedInfo.manufacturer_event_count : 'Automatically calculated')}
                  </span>
                </div>

                <div style={{ backgroundColor: '#ffffff', padding: '0.75rem 1rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                  <span style={{ fontSize: '0.725rem', fontWeight: 600, color: 'var(--text-muted)' }}>Commercial Distribution Volume</span>
                  <span style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--text-primary)', display: 'block', marginTop: '2px' }}>
                    {assessmentResult
                      ? Number(assessmentResult.quantity_in_commerce).toLocaleString()
                      : (derivedInfo.avg_quantity_in_commerce !== null ? Number(derivedInfo.avg_quantity_in_commerce).toLocaleString() : 'Automatically retrieved')}
                  </span>
                </div>
              </div>
            </div>

            {/* SECTION 3: ADDITIONAL INFORMATION (Collapsible Accordion) */}
            <div style={{
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-sm)',
              marginBottom: '2rem',
              overflow: 'hidden',
            }}>
              <button
                type="button"
                onClick={() => setShowAdditional(!showAdditional)}
                style={{
                  width: '100%',
                  padding: '0.85rem 1.25rem',
                  backgroundColor: 'var(--bg-app)',
                  border: 'none',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  cursor: 'pointer',
                  fontSize: '0.9rem',
                  fontWeight: 700,
                  color: 'var(--text-primary)',
                }}
              >
                <span>Additional Information (Optional Parameters)</span>
                {showAdditional ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
              </button>

              {showAdditional && (
                <div style={{ padding: '1.25rem', backgroundColor: '#ffffff' }}>
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
                    Only specify these fields if you wish to override dataset defaults or provide ad-hoc parameters:
                  </p>

                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem' }}>
                    <div className="form-group">
                      <label className="form-label">Country of Event</label>
                      <select
                        className="form-control"
                        name="country_event"
                        value={additionalForm.country_event}
                        onChange={handleAdditionalChange}
                      >
                        <option value="">Dataset incident baseline</option>
                        {options.countries.map((c, idx) => (
                          <option key={idx} value={c}>{c}</option>
                        ))}
                      </select>
                    </div>

                    <div className="form-group">
                      <label className="form-label">Country of Device Origin</label>
                      <select
                        className="form-control"
                        name="country_device"
                        value={additionalForm.country_device}
                        onChange={handleAdditionalChange}
                      >
                        <option value="">Dataset market baseline</option>
                        {options.countries.map((c, idx) => (
                          <option key={idx} value={c}>{c}</option>
                        ))}
                      </select>
                    </div>

                    <div className="form-group">
                      <label className="form-label">Commercial Distribution Volume</label>
                      <input
                        type="number"
                        step="any"
                        min="0"
                        className="form-control"
                        name="quantity_in_commerce"
                        placeholder="e.g. 25000"
                        value={additionalForm.quantity_in_commerce}
                        onChange={handleAdditionalChange}
                      />
                    </div>

                    <div className="form-group">
                      <label className="form-label">Event Year</label>
                      <input
                        type="number"
                        min="1980"
                        max="2035"
                        className="form-control"
                        name="event_year"
                        placeholder="e.g. 2025"
                        value={additionalForm.event_year}
                        onChange={handleAdditionalChange}
                      />
                    </div>

                    <div className="form-group">
                      <label className="form-label">Event Month</label>
                      <input
                        type="number"
                        min="1"
                        max="12"
                        className="form-control"
                        name="event_month"
                        placeholder="1 to 12"
                        value={additionalForm.event_month}
                        onChange={handleAdditionalChange}
                      />
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Action Buttons */}
            <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
              <button
                type="submit"
                className="btn btn-primary"
                style={{ padding: '0.85rem 2.25rem', fontSize: '1rem' }}
                disabled={isSubmitting}
              >
                {isSubmitting ? (
                  <span>Analyzing device information...</span>
                ) : (
                  <>
                    <Activity size={18} />
                    <span>Assess Risk</span>
                  </>
                )}
              </button>

              <button
                type="button"
                onClick={handleResetForm}
                className="btn btn-secondary"
                style={{ padding: '0.85rem 1.5rem' }}
              >
                Reset
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default RiskAssessment;
