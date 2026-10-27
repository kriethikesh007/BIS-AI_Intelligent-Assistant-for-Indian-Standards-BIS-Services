import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Gem,
  CheckCircle2,
  ShieldCheck,
  Search,
  ChevronDown,
  Sparkles,
  FileText,
  HelpCircle,
  QrCode,
  Smartphone,
  ExternalLink,
  Award,
  Scale,
} from 'lucide-react';
import { Card, Badge, Input, Button, PageLoader, ErrorState, EmptyState } from '../components/ui';
import { getHallmarkingData } from '../services/api/endpoints';
import type { HallmarkingResponse, Standard, FAQ } from '../types/api';

/* Static factual Karat Grades data under BIS */
const KARAT_GRADES = [
  {
    grade: '24K999',
    karat: '24 Karat',
    fineness: '999',
    purity: '99.9%',
    description: 'Highest purity bullion, gold coins, and investment bars.',
    badgeColor: 'brand' as const,
    usage: 'Bullion & Investment',
  },
  {
    grade: '23K958',
    karat: '23 Karat',
    fineness: '958',
    purity: '95.8%',
    description: 'High-purity specialized jewelry, religious idols, and medallions.',
    badgeColor: 'brand' as const,
    usage: 'Temple & Specialty Jewelry',
  },
  {
    grade: '22K916',
    karat: '22 Karat',
    fineness: '916',
    purity: '91.6%',
    description: 'Most popular grade for traditional Indian handcrafted jewelry.',
    badgeColor: 'success' as const,
    usage: 'Traditional Gold Jewelry',
  },
  {
    grade: '20K833',
    karat: '20 Karat',
    fineness: '833',
    purity: '83.3%',
    description: 'Durable custom ornaments requiring higher tensile strength.',
    badgeColor: 'info' as const,
    usage: 'Durable Everyday Jewelry',
  },
  {
    grade: '18K750',
    karat: '18 Karat',
    fineness: '750',
    purity: '75.0%',
    description: 'Global standard for diamond-studded, gemstone, and delicate designs.',
    badgeColor: 'warning' as const,
    usage: 'Diamond & Gemstone Jewelry',
  },
  {
    grade: '14K585',
    karat: '14 Karat',
    fineness: '585',
    purity: '58.5%',
    description: 'Resilient and scratch-resistant for lightweight modern daily wear.',
    badgeColor: 'default' as const,
    usage: 'Modern & Lightweight Wear',
  },
];

/* Three Marks of Hallmarking */
const HALLMARK_MARKS = [
  {
    title: '1. BIS Standard Mark',
    description: 'The triangular BIS emblem certifying official compliance with Indian Standards.',
    icon: <Award className="w-4 h-4 text-brand-600 dark:text-brand-400" />,
  },
  {
    title: '2. Purity & Fineness',
    description: 'Clear karat & fineness designation (e.g. 22K916 for 22 Karat / 91.6% purity).',
    icon: <Scale className="w-4 h-4 text-brand-600 dark:text-brand-400" />,
  },
  {
    title: '3. 6-Digit HUID Code',
    description: 'Unique alphanumeric code laser-engraved on each piece for trace-to-origin audit.',
    icon: <QrCode className="w-4 h-4 text-brand-600 dark:text-brand-400" />,
  },
];

export default function HallmarkingPage() {
  const [data, setData] = useState<HallmarkingResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedFaqIndex, setExpandedFaqIndex] = useState<number | null>(null);
  const [faqSearch, setFaqSearch] = useState('');
  const [standardSearch, setStandardSearch] = useState('');

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await getHallmarkingData();
      setData(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch hallmarking information');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

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
          title="Unable to load Hallmarking Data"
          message={error || 'No data was returned from the server.'}
          retry={loadData}
        />
      </div>
    );
  }

  const standardsList: Standard[] = data.standards || [];
  const faqsList: FAQ[] = data.guidelines_and_faqs || [];
  const keyRequirements: string[] = data.key_requirements || [];

  const filteredFaqs = faqsList.filter((faq) => {
    const q = (faq.question || '').toLowerCase();
    const a = (faq.answer || '').toLowerCase();
    const t = (faq.topic || '').toLowerCase();
    const query = faqSearch.toLowerCase();
    return q.includes(query) || a.includes(query) || t.includes(query);
  });

  const filteredStandards = standardsList.filter((std) => {
    const code = (std.standard_code || '').toLowerCase();
    const title = (std.title || '').toLowerCase();
    const desc = (std.scope || std.product || '').toLowerCase();
    const query = standardSearch.toLowerCase();
    return code.includes(query) || title.includes(query) || desc.includes(query);
  });

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-10">
      {/* ─── Hero / Header ─── */}
      <header className="space-y-2">
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="brand" className="gap-1 py-0.5 px-2 text-xs font-medium">
            <Gem className="w-3 h-3" />
            BIS Act 2016 Compliant
          </Badge>
          <Badge variant="success" className="py-0.5 px-2 text-xs font-medium">
            Mandatory Purity Certification
          </Badge>
        </div>
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-semibold tracking-tight text-text-primary">
              Gold & Silver Hallmarking
            </h1>
            <p className="mt-1 text-sm md:text-base text-text-secondary max-w-3xl leading-relaxed">
              Determination and official recording of precious metal content under the Bureau
              of Indian Standards (BIS) Act, 2016. Ensuring verifiable purity and consumer protection.
            </p>
          </div>
          <a
            href="https://www.manakonline.in"
            target="_blank"
            rel="noopener noreferrer"
            className="shrink-0"
          >
            <Button variant="outline" size="sm" icon={<ExternalLink className="w-3.5 h-3.5" />}>
              Manak Online Portal
            </Button>
          </a>
        </div>
      </header>

      {/* ─── Overview & Key Requirements Checklist ─── */}
      <section className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Legal Overview & 3 Marks */}
        <div className="lg:col-span-7 space-y-4">
          <Card className="p-5 space-y-3.5">
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-md bg-brand-500/10 text-brand-600 dark:text-brand-400">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-base font-semibold text-text-primary">
                  Hallmarking Under BIS Act 2016
                </h2>
                <p className="text-[11px] text-text-tertiary">
                  Statutory Regulatory Framework
                </p>
              </div>
            </div>

            <p className="text-xs md:text-sm text-text-secondary leading-relaxed">
              Under Section 14 and Section 16 of the Bureau of Indian Standards Act, 2016, the Central
              Government has notified mandatory hallmarking of gold jewelry and artifacts across
              specified districts. Hallmarking provides an official guarantee of purity and fineness.
            </p>

            <div className="p-3 rounded-md border border-border-subtle bg-bg-secondary text-xs space-y-1.5">
              <h4 className="font-semibold text-[11px] tracking-wider uppercase text-brand-600 dark:text-brand-400">
                Key Statutory Objectives
              </h4>
              <ul className="space-y-1 list-disc list-inside text-text-secondary text-xs">
                <li>Guard against deceptive karat claims and under-caratage by jewelers.</li>
                <li>Ensure uniform assaying via certified Fire Assay testing under IS 1418.</li>
                <li>Empower buyers with end-to-end digital trace-to-origin authentication via HUID.</li>
              </ul>
            </div>
          </Card>

          {/* Three Mandatory Marks Overview */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {HALLMARK_MARKS.map((mark, i) => (
              <Card key={i} className="p-3.5 flex flex-col justify-between">
                <div className="w-8 h-8 rounded-md bg-bg-secondary flex items-center justify-center mb-2 border border-border-subtle">
                  {mark.icon}
                </div>
                <div>
                  <h3 className="text-xs font-semibold mb-1 text-text-primary">
                    {mark.title}
                  </h3>
                  <p className="text-[11px] text-text-secondary leading-relaxed">
                    {mark.description}
                  </p>
                </div>
              </Card>
            ))}
          </div>
        </div>

        {/* Right Column: Key Requirements Checklist */}
        <div className="lg:col-span-5 space-y-4">
          <Card className="p-5 space-y-3.5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                <h3 className="text-sm md:text-base font-semibold text-text-primary">
                  Key Regulatory Checklist
                </h3>
              </div>
              <Badge variant="success" className="text-[11px]">{keyRequirements.length} Items</Badge>
            </div>

            <p className="text-xs text-text-secondary">
              Mandatory criteria that every certified jeweler and Assaying & Hallmarking Centre (AHC) must satisfy:
            </p>

            <ul className="space-y-2 pt-1">
              {keyRequirements.map((req, idx) => (
                <li
                  key={idx}
                  className="flex items-start gap-2.5 p-2.5 rounded-md border border-border-subtle bg-bg-secondary text-xs"
                >
                  <div className="mt-0.5 p-0.5 rounded-full bg-emerald-500/10 text-emerald-500 shrink-0">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                  </div>
                  <span className="text-xs text-text-secondary leading-relaxed">
                    {req}
                  </span>
                </li>
              ))}
            </ul>

            <div className="mt-3 p-2.5 rounded-md border border-brand-500/20 bg-brand-500/5 flex items-center justify-between text-xs">
              <div className="flex items-center gap-2 text-brand-600 dark:text-brand-400">
                <Smartphone className="w-4 h-4" />
                <span className="font-medium">Verify HUID in BIS CARE App</span>
              </div>
              <Badge variant="brand" className="text-[10px]">Free Lookup</Badge>
            </div>
          </Card>
        </div>
      </section>

      {/* ─── HUID Deep Dive Section ─── */}
      <Card className="p-5 md:p-6 space-y-6">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-2 max-w-2xl">
            <div className="flex items-center gap-2">
              <Badge variant="brand" className="gap-1 text-[11px]">
                <Sparkles className="w-3 h-3" />
                Traceability Standard
              </Badge>
              <span className="text-xs text-text-tertiary">
                Mandatory Nationwide
              </span>
            </div>
            <h2 className="text-xl md:text-2xl font-semibold tracking-tight text-text-primary">
              HUID: Hallmarking Unique Identification
            </h2>
            <p className="text-xs md:text-sm text-text-secondary leading-relaxed">
              HUID is a unique 6-digit alphanumeric code laser-engraved onto each piece of jewelry at
              BIS-accredited Assaying and Hallmarking Centres (AHCs). It acts as an indelible digital
              certificate linking the article to the jeweler, assaying center, date, and verified purity.
            </p>
          </div>

          <div className="p-4 rounded-lg border border-border-default bg-bg-secondary flex flex-col items-center text-center max-w-xs w-full shrink-0">
            <div className="text-[10px] uppercase tracking-widest font-mono text-text-tertiary mb-1.5">
              Sample HUID Laser Engraving
            </div>
            <div className="font-mono text-xl font-bold px-4 py-1.5 rounded border border-brand-500/30 bg-bg-primary text-brand-600 dark:text-brand-400 tracking-widest">
              AB12C3
            </div>
            <p className="text-[11px] text-text-tertiary mt-2">
              Marked alongside the BIS triangular emblem & karat grade
            </p>
          </div>
        </div>

        {/* HUID Workflow Steps */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 pt-4 border-t border-border-subtle">
          {[
            {
              step: 'Step 1',
              title: 'Jeweler Dispatch',
              desc: 'Jeweler delivers lot to authorized AHC with automated entry on the portal.',
            },
            {
              step: 'Step 2',
              title: 'Fire Assay Testing',
              desc: 'Specimens are sampled and assayed under IS 1418 strict chemical protocol.',
            },
            {
              step: 'Step 3',
              title: 'Laser Marking',
              desc: 'AHC stamps the BIS Logo, fineness (e.g. 22K916), and unique 6-digit HUID.',
            },
            {
              step: 'Step 4',
              title: 'App Verification',
              desc: 'Consumer enters HUID into BIS CARE app to verify jeweler and center details.',
            },
          ].map((item, idx) => (
            <div
              key={idx}
              className="p-3 rounded-md border border-border-subtle bg-bg-secondary space-y-1"
            >
              <div className="text-[10px] font-bold uppercase tracking-wider text-brand-600 dark:text-brand-400">
                {item.step}
              </div>
              <h4 className="text-xs font-semibold text-text-primary">
                {item.title}
              </h4>
              <p className="text-[11px] text-text-secondary leading-relaxed">
                {item.desc}
              </p>
            </div>
          ))}
        </div>
      </Card>

      {/* ─── Karat Grades Table & Cards ─── */}
      <section className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h2 className="text-lg md:text-xl font-semibold tracking-tight text-text-primary">
              Official BIS Karat Grades & Purity Fineness
            </h2>
            <p className="text-xs text-text-secondary">
              Standard fineness denominations recognized under Indian Standard IS 1417
            </p>
          </div>
          <Badge variant="info" className="text-xs">6 Recognized Grades</Badge>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {KARAT_GRADES.map((kg) => (
            <Card
              key={kg.grade}
              className="p-4 flex flex-col justify-between space-y-3 hover:border-border-strong transition-colors"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="font-mono text-base font-bold text-text-primary">
                    {kg.grade}
                  </span>
                  <Badge variant={kg.badgeColor} className="text-[11px]">{kg.purity} Gold</Badge>
                </div>
                <div className="space-y-0.5">
                  <div className="text-xs font-semibold text-text-primary">
                    {kg.karat} ({kg.fineness} / 1000)
                  </div>
                  <div className="text-[11px] text-brand-600 dark:text-brand-400 font-medium">
                    {kg.usage}
                  </div>
                  <p className="text-xs text-text-secondary leading-relaxed pt-1.5">
                    {kg.description}
                  </p>
                </div>
              </div>

              <div className="pt-2.5 border-t border-border-subtle flex items-center justify-between text-[11px] text-text-tertiary">
                <span>Fineness: {kg.fineness} ppt</span>
                <span>Purity: {kg.purity}</span>
              </div>
            </Card>
          ))}
        </div>
      </section>

      {/* ─── Standards List Cards ─── */}
      <section className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-1.5">
              <FileText className="w-4 h-4 text-brand-600 dark:text-brand-400" />
              <h2 className="text-lg md:text-xl font-semibold tracking-tight text-text-primary">
                Applicable Standards & Specifications
              </h2>
            </div>
            <p className="text-xs text-text-secondary">
              Indian Standards governing precious metal purity, assaying procedures, and marking
            </p>
          </div>
          <div className="w-full sm:w-64">
            <Input
              icon={<Search className="w-3.5 h-3.5" />}
              placeholder="Filter (e.g. IS 1417)..."
              value={standardSearch}
              onChange={(e) => setStandardSearch(e.target.value)}
            />
          </div>
        </div>

        {filteredStandards.length === 0 ? (
          <EmptyState
            icon={<FileText className="w-7 h-7" />}
            title="No standards found"
            description={
              standardSearch
                ? `No standards matched "${standardSearch}". Clear your search to see all records.`
                : 'No hallmarking standards are currently registered in the database.'
            }
            action={
              standardSearch ? (
                <Button variant="secondary" size="sm" onClick={() => setStandardSearch('')}>
                  Clear filter
                </Button>
              ) : undefined
            }
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {filteredStandards.map((std, i) => (
              <Card
                key={std.id || std.standard_code || i}
                className="p-4 space-y-2.5 flex flex-col justify-between"
              >
                <div className="space-y-1.5">
                  <div className="flex items-start justify-between gap-3">
                    <span className="font-mono text-xs font-bold px-2 py-0.5 rounded border border-border-subtle bg-bg-secondary text-brand-600 dark:text-brand-400">
                      {std.standard_code}
                    </span>
                    {std.mandatory_status && (
                      <Badge
                        variant={
                          std.mandatory_status.toLowerCase().includes('mandatory')
                            ? 'warning'
                            : 'default'
                        }
                        className="text-[11px]"
                      >
                        {std.mandatory_status}
                      </Badge>
                    )}
                  </div>
                  <h3 className="text-sm font-semibold leading-snug text-text-primary">
                    {std.title}
                  </h3>
                  {std.scope && (
                    <p className="text-xs text-text-secondary leading-relaxed line-clamp-2">
                      {std.scope}
                    </p>
                  )}
                </div>

                <div className="pt-2 border-t border-border-subtle flex flex-wrap items-center justify-between gap-2 text-[11px] text-text-tertiary">
                  <div className="flex items-center gap-2">
                    {std.category && <span>{std.category}</span>}
                    {std.certification_scheme && (
                      <span>• Scheme: {std.certification_scheme}</span>
                    )}
                  </div>
                  {std.reference_document && (
                    <span className="truncate max-w-[180px]" title={std.reference_document}>
                      Ref: {std.reference_document}
                    </span>
                  )}
                </div>
              </Card>
            ))}
          </div>
        )}
      </section>

      {/* ─── Expandable FAQs Section ─── */}
      <section className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-1.5">
              <HelpCircle className="w-4 h-4 text-brand-600 dark:text-brand-400" />
              <h2 className="text-lg md:text-xl font-semibold tracking-tight text-text-primary">
                Frequently Asked Questions
              </h2>
            </div>
            <p className="text-xs text-text-secondary">
              Common queries regarding hallmarking regulations, consumer rights, and validation
            </p>
          </div>
          <div className="w-full sm:w-64">
            <Input
              icon={<Search className="w-3.5 h-3.5" />}
              placeholder="Search FAQs..."
              value={faqSearch}
              onChange={(e) => setFaqSearch(e.target.value)}
            />
          </div>
        </div>

        {filteredFaqs.length === 0 ? (
          <EmptyState
            icon={<HelpCircle className="w-7 h-7" />}
            title="No FAQs found"
            description={
              faqSearch
                ? `No questions matched "${faqSearch}". Try different keywords.`
                : 'No FAQs are currently available for hallmarking.'
            }
            action={
              faqSearch ? (
                <Button variant="secondary" size="sm" onClick={() => setFaqSearch('')}>
                  Clear search
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
                          {faq.question || 'Hallmarking Query'}
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
                          {faq.source && (
                            <div className="pt-2 text-[10px] text-text-tertiary flex items-center gap-1">
                              <span>Source:</span>
                              <span className="font-mono">{faq.source}</span>
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

      {/* ─── Footer Verification Banner ─── */}
      <Card className="p-5 flex flex-col sm:flex-row items-center justify-between gap-4 bg-bg-secondary border-border-default">
        <div className="flex items-center gap-3 text-center sm:text-left">
          <div className="p-2.5 rounded-lg bg-brand-500/10 text-brand-600 dark:text-brand-400 shrink-0 hidden sm:block">
            <Smartphone className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-text-primary">
              Verify gold authenticity on your mobile device
            </h4>
            <p className="text-xs text-text-secondary mt-0.5">
              Download the official BIS CARE App from Google Play Store or Apple App Store and input
              the 6-digit laser HUID code.
            </p>
          </div>
        </div>
        <a
          href="https://play.google.com/store/apps/details?id=com.bis.biscare"
          target="_blank"
          rel="noopener noreferrer"
          className="shrink-0"
        >
          <Button variant="primary" size="sm" icon={<Smartphone className="w-3.5 h-3.5" />}>
            Get BIS CARE App
          </Button>
        </a>
      </Card>
    </div>
  );
}
