import { useState, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ShieldCheck,
  Smartphone,
  HelpCircle,
  Search,
  ExternalLink,
  ChevronDown,
  AlertTriangle,
  CheckCircle2,
  PhoneCall,
  Scale,
  QrCode,
  BookOpen,
} from 'lucide-react';
import { Card, Badge, Input, Button, PageLoader, ErrorState, EmptyState } from '../components/ui';
import { getConsumerData } from '../services/api/endpoints';
import type { ConsumerResponse, FAQ } from '../types/api';

/* Essential Consumer Rights under BIS & Consumer Protection Act 2019 */
const CONSUMER_RIGHTS = [
  {
    title: 'Right to Safety',
    description: 'Protection against hazardous, defective, or substandard goods not conforming to Indian Standards.',
    icon: <ShieldCheck className="w-4 h-4 text-brand-600 dark:text-brand-400" />,
  },
  {
    title: 'Right to Information',
    description: 'Entitlement to verified details regarding purity, potency, grade, and genuine BIS license validity.',
    icon: <BookOpen className="w-4 h-4 text-brand-600 dark:text-brand-400" />,
  },
  {
    title: 'Right to Redressal',
    description: 'Legal recourse against unfair trade practices, counterfeit ISI marks, or substandard certified articles.',
    icon: <Scale className="w-4 h-4 text-brand-600 dark:text-brand-400" />,
  },
  {
    title: 'Right to Authenticity',
    description: 'Direct verification of 6-digit HUID for jewelry and CML/R numbers via the BIS CARE application.',
    icon: <QrCode className="w-4 h-4 text-brand-600 dark:text-brand-400" />,
  },
];

/* Official Consumer Portals */
const CONSUMER_PORTALS = [
  {
    name: 'BIS Manak Online',
    description: 'Official portal to verify ISI licenses, hallmarking centers, and laboratory accreditation.',
    url: 'https://www.manakonline.in',
    badge: 'Official BIS Portal',
  },
  {
    name: 'National Consumer Helpline (NCH)',
    description: 'Government grievance redressal helpline. Call toll-free 1915 or lodge online complaints.',
    url: 'https://consumerhelpline.gov.in',
    badge: 'Toll-free 1915',
  },
  {
    name: 'e-Daakhil Portal',
    description: 'Online filing of consumer disputes and grievances directly to Consumer Commissions.',
    url: 'https://edaakhil.nic.in',
    badge: 'Legal Redressal',
  },
  {
    name: 'Know Your Standards (KYS)',
    description: 'Search, read, and verify Indian Standards for consumer goods and technical specifications.',
    url: 'https://standardsbis.bsbedge.com',
    badge: 'Free Viewing',
  },
];

/* Steps to lodge a complaint */
const GRIEVANCE_STEPS = [
  {
    step: '1',
    title: 'Inspect & Gather Proof',
    desc: 'Capture photos of the product, packaging, counterfeit ISI/BIS mark, batch number, and purchase invoice.',
  },
  {
    step: '2',
    title: 'Verify via BIS CARE',
    desc: 'Input the CML or HUID number in the app. If invalid or unlicensed, click "Lodge Complaint".',
  },
  {
    step: '3',
    title: 'BIS Enforcement Raid',
    desc: 'BIS enforcement teams investigate, conduct search & seizure raids, and initiate prosecution in court.',
  },
  {
    step: '4',
    title: 'Resolution & Penalty',
    desc: 'Penalties under Section 29 of the BIS Act, 2016 include imprisonment up to 2 years and statutory fines.',
  },
];

export default function ConsumerPage() {
  const [data, setData] = useState<ConsumerResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // FAQ interactive states
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTopic, setSelectedTopic] = useState('All');
  const [expandedFaqIndex, setExpandedFaqIndex] = useState<number | null>(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await getConsumerData();
      setData(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch consumer protection data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const faqsList: FAQ[] = useMemo(() => {
    if (!data) return [];
    return data.consumer_resources || data.faqs || [];
  }, [data]);

  const topics = useMemo(() => {
    const topicSet = new Set<string>();
    faqsList.forEach((faq) => {
      if (faq.topic && faq.topic.trim()) {
        topicSet.add(faq.topic.trim());
      }
    });
    return ['All', ...Array.from(topicSet).sort()];
  }, [faqsList]);

  const filteredFaqs = useMemo(() => {
    return faqsList.filter((faq) => {
      const matchesTopic =
        selectedTopic === 'All' ||
        (faq.topic && faq.topic.toLowerCase() === selectedTopic.toLowerCase());

      if (!matchesTopic) return false;

      const q = (faq.question || '').toLowerCase();
      const a = (faq.answer || '').toLowerCase();
      const t = (faq.topic || '').toLowerCase();
      const query = searchQuery.trim().toLowerCase();

      if (query) {
        return q.includes(query) || a.includes(query) || t.includes(query);
      }

      return true;
    });
  }, [faqsList, selectedTopic, searchQuery]);

  const toggleFaq = (index: number) => {
    setExpandedFaqIndex((prev) => (prev === index ? null : index));
  };

  if (loading) {
    return <PageLoader />;
  }

  if (error || !data) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-8">
        <ErrorState
          title="Unable to load Consumer Protection Data"
          message={error || 'No response received from the consumer API service.'}
          retry={loadData}
        />
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-10">
      {/* ─── Hero / Header ─── */}
      <header className="space-y-2">
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="brand" className="gap-1 py-0.5 px-2 text-xs font-medium">
            <ShieldCheck className="w-3 h-3" />
            Consumer Protection & Grievances
          </Badge>
          <Badge variant="success" className="py-0.5 px-2 text-xs font-medium">
            BIS Act 2016 & CPA 2019
          </Badge>
        </div>

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-semibold tracking-tight text-text-primary">
              Consumer Rights & Protection
            </h1>
            <p className="mt-1 text-sm md:text-base text-text-secondary max-w-3xl leading-relaxed">
              Empowering consumers across India to verify standard marks, validate gold hallmarking
              purity, check laboratory test reports, and report counterfeit or substandard articles.
            </p>
          </div>

          <a
            href="https://consumerhelpline.gov.in"
            target="_blank"
            rel="noopener noreferrer"
            className="shrink-0"
          >
            <Button variant="outline" size="sm" icon={<PhoneCall className="w-3.5 h-3.5" />}>
              National Helpline (1915)
            </Button>
          </a>
        </div>
      </header>

      {/* ─── Consumer Rights Overview ─── */}
      <section className="space-y-3.5">
        <div>
          <h2 className="text-lg md:text-xl font-semibold tracking-tight text-text-primary">
            Consumer Rights Under Bureau of Indian Standards
          </h2>
          <p className="text-xs text-text-secondary">
            Statutory protections guaranteed under Indian law for certified goods and services
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {CONSUMER_RIGHTS.map((right, idx) => (
            <Card
              key={idx}
              className="p-4 space-y-2.5 flex flex-col justify-between hover:border-border-strong transition-colors"
            >
              <div className="space-y-2">
                <div className="w-8 h-8 rounded-md bg-bg-secondary flex items-center justify-center border border-border-subtle">
                  {right.icon}
                </div>
                <h3 className="text-sm font-semibold text-text-primary">
                  {right.title}
                </h3>
                <p className="text-xs text-text-secondary leading-relaxed">
                  {right.description}
                </p>
              </div>
            </Card>
          ))}
        </div>
      </section>

      {/* ─── BIS CARE Mobile Application Showcase ─── */}
      <Card className="p-5 md:p-6 space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
          {/* Left Text Column */}
          <div className="lg:col-span-7 space-y-4">
            <div className="flex items-center gap-2">
              <Badge variant="brand" className="gap-1 text-[11px]">
                <Smartphone className="w-3 h-3" />
                Citizen Portal
              </Badge>
              <span className="text-xs text-text-tertiary">
                Free on Android & iOS
              </span>
            </div>

            <h2 className="text-xl md:text-2xl font-semibold tracking-tight text-text-primary">
              BIS CARE Mobile Application
            </h2>

            <p className="text-xs md:text-sm text-text-secondary leading-relaxed">
              The <strong>BIS CARE</strong> mobile application is the primary citizen-facing tool
              developed by the Bureau of Indian Standards. It lets citizens verify the authenticity
              of any standard mark, gold hallmarking, or electronic registration instantly on their
              smartphones.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 pt-1">
              <div className="p-3 rounded-md border border-border-subtle bg-bg-secondary flex items-start gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0 mt-0.5" />
                <div>
                  <h4 className="text-xs font-semibold text-text-primary">
                    Verify ISI License (CML)
                  </h4>
                  <p className="text-[11px] text-text-secondary mt-0.5">
                    Enter the 7 or 8-digit CML number on the product to check manufacturer validity.
                  </p>
                </div>
              </div>

              <div className="p-3 rounded-md border border-border-subtle bg-bg-secondary flex items-start gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0 mt-0.5" />
                <div>
                  <h4 className="text-xs font-semibold text-text-primary">
                    Verify 6-Digit HUID
                  </h4>
                  <p className="text-[11px] text-text-secondary mt-0.5">
                    Input 6-digit laser code on jewelry to view jeweler name, AHC center, and karatage.
                  </p>
                </div>
              </div>

              <div className="p-3 rounded-md border border-border-subtle bg-bg-secondary flex items-start gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0 mt-0.5" />
                <div>
                  <h4 className="text-xs font-semibold text-text-primary">
                    Verify CRS Registration (R-No)
                  </h4>
                  <p className="text-[11px] text-text-secondary mt-0.5">
                    Validate electronics & IT hardware registrations under Compulsory Registration.
                  </p>
                </div>
              </div>

              <div className="p-3 rounded-md border border-border-subtle bg-bg-secondary flex items-start gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0 mt-0.5" />
                <div>
                  <h4 className="text-xs font-semibold text-text-primary">
                    Lodge Direct Complaints
                  </h4>
                  <p className="text-[11px] text-text-secondary mt-0.5">
                    Report fake marks, substandard quality, or deceptive claims to enforcement officers.
                  </p>
                </div>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-2.5 pt-2">
              <a
                href="https://play.google.com/store/apps/details?id=com.bis.biscare"
                target="_blank"
                rel="noopener noreferrer"
              >
                <Button variant="primary" size="sm" icon={<Smartphone className="w-3.5 h-3.5" />}>
                  Download on Google Play
                </Button>
              </a>
              <a
                href="https://apps.apple.com/in/app/bis-care/id1534003260"
                target="_blank"
                rel="noopener noreferrer"
              >
                <Button variant="outline" size="sm" icon={<ExternalLink className="w-3.5 h-3.5" />}>
                  Download on App Store
                </Button>
              </a>
            </div>
          </div>

          {/* Right Visual Card */}
          <div className="lg:col-span-5 flex justify-center">
            <div className="p-5 rounded-lg border border-border-default bg-bg-primary w-full max-w-sm space-y-3.5">
              <div className="flex items-center justify-between pb-2.5 border-t-0 border-b border-border-subtle">
                <span className="font-semibold text-xs text-text-primary">
                  BIS CARE Quick Verification
                </span>
                <Badge variant="success" className="text-[10px]">Verified Engine</Badge>
              </div>

              <div className="space-y-2 text-xs">
                <div className="p-2.5 rounded border border-border-subtle bg-bg-secondary space-y-0.5">
                  <span className="text-[10px] font-semibold uppercase tracking-wider block text-text-tertiary">
                    ISI License (CML Number)
                  </span>
                  <div className="font-mono text-xs text-brand-600 dark:text-brand-400 font-semibold">
                    CM/L-1234567 (7 or 8 digits)
                  </div>
                </div>

                <div className="p-2.5 rounded border border-border-subtle bg-bg-secondary space-y-0.5">
                  <span className="text-[10px] font-semibold uppercase tracking-wider block text-text-tertiary">
                    Hallmark Gold Verification
                  </span>
                  <div className="font-mono text-xs text-brand-600 dark:text-brand-400 font-semibold">
                    AB12C3 (6-Digit HUID)
                  </div>
                </div>

                <div className="p-2.5 rounded border border-border-subtle bg-bg-secondary space-y-0.5">
                  <span className="text-[10px] font-semibold uppercase tracking-wider block text-text-tertiary">
                    Electronics Registration
                  </span>
                  <div className="font-mono text-xs text-brand-600 dark:text-brand-400 font-semibold">
                    R-41012345 (CRS Portal)
                  </div>
                </div>
              </div>

              <div className="p-2 rounded text-center text-[11px] font-medium bg-brand-500/5 text-brand-600 dark:text-brand-400 border border-brand-500/20">
                Official Consumer Verification System
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* ─── How to Lodge a Consumer Complaint ─── */}
      <section className="space-y-3.5">
        <div>
          <div className="flex items-center gap-1.5">
            <AlertTriangle className="w-4 h-4 text-amber-500" />
            <h2 className="text-lg md:text-xl font-semibold tracking-tight text-text-primary">
              How to Lodge a Consumer Complaint
            </h2>
          </div>
          <p className="text-xs text-text-secondary">
            4-step protocol for reporting counterfeit goods, substandard products, or deceptive BIS marks
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
          {GRIEVANCE_STEPS.map((step) => (
            <Card key={step.step} className="p-3.5 space-y-1.5">
              <div className="text-[10px] font-bold uppercase tracking-wider flex items-center justify-between text-brand-600 dark:text-brand-400">
                <span>Step {step.step}</span>
                <span className="w-5 h-5 rounded-full flex items-center justify-center text-[10px] bg-brand-500 text-white font-bold">
                  {step.step}
                </span>
              </div>
              <h3 className="text-xs font-semibold text-text-primary">
                {step.title}
              </h3>
              <p className="text-[11px] text-text-secondary leading-relaxed">
                {step.desc}
              </p>
            </Card>
          ))}
        </div>
      </section>

      {/* ─── Official Portals & Verification Resources ─── */}
      <section className="space-y-3.5">
        <div>
          <h2 className="text-lg md:text-xl font-semibold tracking-tight text-text-primary">
            Verification Portals & Consumer Helplines
          </h2>
          <p className="text-xs text-text-secondary">
            Government gateways for standards verification and legal consumer redressal
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {CONSUMER_PORTALS.map((portal) => (
            <Card
              key={portal.name}
              className="p-4 flex flex-col justify-between space-y-3 hover:border-border-strong transition-colors"
            >
              <div className="space-y-1.5">
                <Badge variant="brand" className="text-[10px]">
                  {portal.badge}
                </Badge>
                <h3 className="text-xs font-semibold text-text-primary">
                  {portal.name}
                </h3>
                <p className="text-[11px] text-text-secondary leading-relaxed">
                  {portal.description}
                </p>
              </div>

              <a
                href={portal.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-xs font-medium text-brand-600 dark:text-brand-400 hover:underline pt-2 border-t border-border-subtle"
              >
                <span>Visit Portal</span>
                <ExternalLink className="w-3 h-3" />
              </a>
            </Card>
          ))}
        </div>
      </section>

      {/* ─── Expandable FAQs Grouped by Topic ─── */}
      <section className="space-y-3.5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-1.5">
              <HelpCircle className="w-4 h-4 text-brand-600 dark:text-brand-400" />
              <h2 className="text-lg md:text-xl font-semibold tracking-tight text-text-primary">
                Consumer Help FAQs
              </h2>
            </div>
            <p className="text-xs text-text-secondary">
              Questions on grievance procedures, ISI marks, and mandatory quality control orders
            </p>
          </div>

          <div className="w-full sm:w-64">
            <Input
              icon={<Search className="w-3.5 h-3.5" />}
              placeholder="Search questions..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </div>

        {/* Topic filter tabs */}
        {topics.length > 1 && (
          <div className="flex flex-wrap gap-1.5">
            {topics.map((topic) => {
              const isSelected = selectedTopic === topic;
              return (
                <button
                  key={topic}
                  type="button"
                  onClick={() => setSelectedTopic(topic)}
                  className={`px-2.5 py-1 rounded-md text-xs font-medium transition-colors border ${
                    isSelected
                      ? 'bg-brand-500 text-white border-brand-500'
                      : 'bg-bg-secondary text-text-secondary border-border-subtle hover:text-text-primary'
                  }`}
                >
                  {topic}
                </button>
              );
            })}
          </div>
        )}

        {/* FAQs List */}
        {filteredFaqs.length === 0 ? (
          <EmptyState
            icon={<HelpCircle className="w-7 h-7" />}
            title="No questions found"
            description={
              searchQuery || selectedTopic !== 'All'
                ? `No FAQs matched your filters. Try adjusting your search query or selecting a different topic.`
                : 'No consumer FAQs are currently available.'
            }
            action={
              searchQuery || selectedTopic !== 'All' ? (
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => {
                    setSearchQuery('');
                    setSelectedTopic('All');
                  }}
                >
                  Clear filters
                </Button>
              ) : undefined
            }
          />
        ) : (
          <div className="space-y-2">
            {filteredFaqs.map((faq, index) => {
              const isExpanded = expandedFaqIndex === index;
              return (
                <Card
                  key={faq.id || index}
                  className="transition-colors overflow-hidden"
                  padding="none"
                >
                  <button
                    type="button"
                    onClick={() => toggleFaq(index)}
                    className="w-full flex items-center justify-between p-4 text-left cursor-pointer hover:bg-bg-secondary/40 transition-colors"
                    aria-expanded={isExpanded}
                  >
                    <div className="flex items-start gap-2.5 pr-4">
                      <HelpCircle className="w-4 h-4 text-brand-600 dark:text-brand-400 shrink-0 mt-0.5" />
                      <div>
                        <span className="text-xs md:text-sm font-semibold text-text-primary block leading-snug">
                          {faq.question || 'Consumer Query'}
                        </span>
                        {faq.topic && (
                          <span className="inline-block mt-1 text-[10px] text-text-tertiary">
                            Topic: {faq.topic}
                          </span>
                        )}
                      </div>
                    </div>
                    <motion.div
                      animate={{ rotate: isExpanded ? 180 : 0 }}
                      transition={{ duration: 0.18 }}
                      className="shrink-0 text-text-tertiary"
                    >
                      <ChevronDown className="w-4 h-4" />
                    </motion.div>
                  </button>

                  <AnimatePresence initial={false}>
                    {isExpanded && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.18 }}
                        className="overflow-hidden"
                      >
                        <div className="px-4 pb-4 pt-1 text-xs text-text-secondary leading-relaxed border-t border-border-subtle bg-bg-secondary/30">
                          <p className="whitespace-pre-line pt-2">{faq.answer}</p>
                          {Boolean(faq.source || (faq as Record<string, unknown>).source_document) && (
                            <div className="pt-2 text-[10px] text-text-tertiary flex items-center gap-1">
                              <span>Reference:</span>
                              <span className="font-mono">
                                {faq.source || String((faq as Record<string, unknown>).source_document || '')}
                              </span>
                            </div>
                          )}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </Card>
              );
            })}
          </div>
        )}
      </section>

      {/* ─── Bottom Grievance Helpline Card ─── */}
      <Card className="p-5 flex flex-col sm:flex-row items-center justify-between gap-4 bg-bg-secondary border-border-default">
        <div className="flex items-center gap-3 text-center sm:text-left">
          <div className="p-2.5 rounded-lg bg-brand-500/10 text-brand-600 dark:text-brand-400 shrink-0 hidden sm:block">
            <PhoneCall className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-text-primary">
              Need immediate consumer grievance assistance?
            </h4>
            <p className="text-xs text-text-secondary mt-0.5">
              Call the National Consumer Helpline at <strong>1915</strong> (Toll Free) or write to{' '}
              <strong>complaints@bis.gov.in</strong>.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <a href="tel:1915">
            <Button variant="primary" size="sm" icon={<PhoneCall className="w-3.5 h-3.5" />}>
              Call 1915
            </Button>
          </a>
        </div>
      </Card>
    </div>
  );
}
