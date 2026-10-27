import { useState, useEffect, useMemo, useCallback } from 'react';
import {
  FlaskConical,
  Search,
  MapPin,
  Phone,
  Mail,
  ExternalLink,
  ShieldCheck,
  Tag,
  Filter,
  X,
  Building2,
} from 'lucide-react';
import { Card, Badge, Input, Button, PageLoader, ErrorState, EmptyState } from '../components/ui';
import { getLaboratories } from '../services/api/endpoints';
import type { Laboratory, LaboratoriesResponse } from '../types/api';

/* Helper to parse email from string or object */
function extractEmail(lab: Laboratory): string | undefined {
  if (lab.email) return lab.email;
  if (typeof lab.contact === 'string') {
    const match = lab.contact.match(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/);
    if (match) return match[0];
  }
  return undefined;
}

/* Helper to parse phone number from string or object */
function extractPhone(lab: Laboratory): string | undefined {
  if (lab.phone) return lab.phone;
  if (typeof lab.contact === 'string') {
    const match = lab.contact.match(/(?:\+?\d{1,4}[- ]?)?\(?\d{2,5}\)?[- ]?\d{5,8}/);
    if (match) return match[0];
  }
  return undefined;
}

/* Helper to extract website */
function extractWebsite(lab: Laboratory): string | undefined {
  if (lab.website) return lab.website;
  const sourceUrl = (lab as Record<string, unknown>).source_url;
  if (typeof sourceUrl === 'string' && sourceUrl.startsWith('http')) {
    return sourceUrl;
  }
  return undefined;
}

/* Helper to determine badge variant for lab type */
function getLabTypeVariant(type?: string): 'brand' | 'success' | 'warning' | 'info' | 'default' {
  if (!type) return 'default';
  const lower = type.toLowerCase();
  if (lower.includes('central') || lower.includes('apex')) return 'brand';
  if (lower.includes('regional')) return 'info';
  if (lower.includes('branch')) return 'success';
  if (lower.includes('recognized') || lower.includes('external')) return 'warning';
  return 'default';
}

export default function LaboratoryPage() {
  const [laboratories, setLaboratories] = useState<Laboratory[]>([]);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filter states
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedState, setSelectedState] = useState('');
  const [selectedCity, setSelectedCity] = useState('');
  const [selectedDiscipline, setSelectedDiscipline] = useState('');

  // Fetch labs from backend
  const fetchLabs = useCallback(async (stateFilter?: string, cityFilter?: string) => {
    setLoading(true);
    setError(null);
    try {
      const filters = {
        state: stateFilter ? stateFilter : undefined,
        city: cityFilter ? cityFilter : undefined,
      };
      const res: LaboratoriesResponse = await getLaboratories(filters);
      setLaboratories(res.laboratories || []);
      setTotalCount(res.total ?? (res.laboratories?.length || 0));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch laboratory network directory');
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial load
  useEffect(() => {
    fetchLabs(selectedState, selectedCity);
  }, [fetchLabs, selectedState, selectedCity]);

  // Extract unique states from loaded labs
  const availableStates = useMemo(() => {
    const states = new Set<string>();
    laboratories.forEach((l) => {
      if (l.state) states.add(l.state.trim());
    });
    return Array.from(states).sort();
  }, [laboratories]);

  // Extract unique cities based on selected state
  const availableCities = useMemo(() => {
    const cities = new Set<string>();
    laboratories.forEach((l) => {
      if (!selectedState || (l.state && l.state.toLowerCase().includes(selectedState.toLowerCase()))) {
        if (l.city) cities.add(l.city.trim());
      }
    });
    return Array.from(cities).sort();
  }, [laboratories, selectedState]);

  // Extract unique disciplines
  const availableDisciplines = useMemo(() => {
    const disciplines = new Set<string>();
    laboratories.forEach((l) => {
      if (Array.isArray(l.disciplines)) {
        l.disciplines.forEach((d) => disciplines.add(d.trim()));
      }
    });
    return Array.from(disciplines).sort();
  }, [laboratories]);

  // Client-side text & discipline filtering
  const filteredLabs = useMemo(() => {
    return laboratories.filter((lab) => {
      const labName = (lab.name || lab.lab_name || '').toLowerCase();
      const labAddress = (lab.address || '').toLowerCase();
      const labCity = (lab.city || '').toLowerCase();
      const labState = (lab.state || '').toLowerCase();
      const labType = (lab.type || '').toLowerCase();
      const labAccreditation = (lab.accreditation || '').toLowerCase();
      const testedProducts = Array.isArray((lab as Record<string, unknown>).tested_products)
        ? ((lab as Record<string, unknown>).tested_products as string[]).join(' ').toLowerCase()
        : '';
      const disciplines = Array.isArray(lab.disciplines) ? lab.disciplines.join(' ').toLowerCase() : '';

      const query = searchQuery.trim().toLowerCase();
      if (query) {
        const matchesQuery =
          labName.includes(query) ||
          labAddress.includes(query) ||
          labCity.includes(query) ||
          labState.includes(query) ||
          labType.includes(query) ||
          labAccreditation.includes(query) ||
          testedProducts.includes(query) ||
          disciplines.includes(query);

        if (!matchesQuery) return false;
      }

      if (selectedDiscipline) {
        if (!Array.isArray(lab.disciplines) || !lab.disciplines.some((d) => d.toLowerCase() === selectedDiscipline.toLowerCase())) {
          return false;
        }
      }

      return true;
    });
  }, [laboratories, searchQuery, selectedDiscipline]);

  const handleResetFilters = () => {
    setSearchQuery('');
    setSelectedState('');
    setSelectedCity('');
    setSelectedDiscipline('');
  };

  const hasActiveFilters = Boolean(searchQuery || selectedState || selectedCity || selectedDiscipline);

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-6">
      {/* ─── Page Header ─── */}
      <header className="space-y-2">
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="brand" className="gap-1 py-0.5 px-2 text-xs font-medium">
            <FlaskConical className="w-3 h-3" />
            Testing & Calibration Network
          </Badge>
          <Badge variant="info" className="py-0.5 px-2 text-xs font-medium">
            IS/ISO/IEC 17025 Accredited
          </Badge>
        </div>

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-semibold tracking-tight text-text-primary">
              BIS Laboratory Network
            </h1>
            <p className="mt-1 text-sm md:text-base text-text-secondary max-w-3xl leading-relaxed">
              Explore Central, Regional, Branch, and recognized testing laboratories equipped for
              conformity assessment, chemical analysis, mechanical testing, and certification audits.
            </p>
          </div>

          <a
            href="https://www.bis.gov.in/laboratories/bis-laboratories/"
            target="_blank"
            rel="noopener noreferrer"
            className="shrink-0"
          >
            <Button variant="outline" size="sm" icon={<ExternalLink className="w-3.5 h-3.5" />}>
              Official Lab Directory
            </Button>
          </a>
        </div>
      </header>

      {/* ─── Search & Filters Bar ─── */}
      <Card className="p-4 md:p-5 space-y-3.5">
        <div className="grid grid-cols-1 md:grid-cols-12 gap-2.5">
          {/* Main Search Input */}
          <div className="md:col-span-5">
            <Input
              icon={<Search className="w-3.5 h-3.5" />}
              placeholder="Search by name, product, city, or discipline..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          {/* State Filter */}
          <div className="md:col-span-3">
            <div className="relative">
              <select
                value={selectedState}
                onChange={(e) => {
                  setSelectedState(e.target.value);
                  setSelectedCity('');
                }}
                className="w-full h-9 px-3 text-xs md:text-sm rounded-md border border-border-default bg-bg-primary text-text-primary outline-none transition-colors appearance-none pr-8 cursor-pointer focus:border-brand-500 focus:ring-1 focus:ring-brand-500/20"
              >
                <option value="">All States / Regions</option>
                {availableStates.map((st) => (
                  <option key={st} value={st}>
                    {st}
                  </option>
                ))}
              </select>
              <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2.5 text-text-tertiary">
                <Filter className="w-3.5 h-3.5" />
              </div>
            </div>
          </div>

          {/* City Filter */}
          <div className="md:col-span-2">
            <div className="relative">
              <select
                value={selectedCity}
                onChange={(e) => setSelectedCity(e.target.value)}
                className="w-full h-9 px-3 text-xs md:text-sm rounded-md border border-border-default bg-bg-primary text-text-primary outline-none transition-colors appearance-none pr-8 cursor-pointer focus:border-brand-500 focus:ring-1 focus:ring-brand-500/20"
              >
                <option value="">All Cities</option>
                {availableCities.map((ct) => (
                  <option key={ct} value={ct}>
                    {ct}
                  </option>
                ))}
              </select>
              <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2.5 text-text-tertiary">
                <MapPin className="w-3.5 h-3.5" />
              </div>
            </div>
          </div>

          {/* Discipline Filter */}
          <div className="md:col-span-2">
            <div className="relative">
              <select
                value={selectedDiscipline}
                onChange={(e) => setSelectedDiscipline(e.target.value)}
                className="w-full h-9 px-3 text-xs md:text-sm rounded-md border border-border-default bg-bg-primary text-text-primary outline-none transition-colors appearance-none pr-8 cursor-pointer focus:border-brand-500 focus:ring-1 focus:ring-brand-500/20"
              >
                <option value="">All Disciplines</option>
                {availableDisciplines.map((disc) => (
                  <option key={disc} value={disc}>
                    {disc}
                  </option>
                ))}
              </select>
              <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2.5 text-text-tertiary">
                <Tag className="w-3.5 h-3.5" />
              </div>
            </div>
          </div>
        </div>

        {/* Results summary and Active Filters bar */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-2.5 border-t border-border-subtle text-xs">
          <div className="flex items-center gap-2">
            <span className="text-text-secondary">
              Showing <strong className="text-text-primary">{filteredLabs.length}</strong> of{' '}
              <strong className="text-text-primary">{totalCount}</strong> laboratories
            </span>
            {hasActiveFilters && (
              <Badge variant="brand" className="text-[10px]">
                Filtered
              </Badge>
            )}
          </div>

          {hasActiveFilters && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleResetFilters}
              icon={<X className="w-3 h-3" />}
              className="h-6 text-xs px-2"
            >
              Reset all filters
            </Button>
          )}
        </div>
      </Card>

      {/* ─── Laboratory Cards Grid ─── */}
      {loading ? (
        <PageLoader />
      ) : error ? (
        <ErrorState
          title="Error Loading Laboratories"
          message={error}
          retry={() => fetchLabs(selectedState, selectedCity)}
        />
      ) : filteredLabs.length === 0 ? (
        <EmptyState
          icon={<FlaskConical className="w-8 h-8" />}
          title="No laboratories found"
          description={
            hasActiveFilters
              ? 'No laboratories match your current search and filter criteria. Try clearing some filters.'
              : 'No laboratories are currently registered in the database.'
          }
          action={
            hasActiveFilters ? (
              <Button variant="secondary" size="sm" onClick={handleResetFilters}>
                Reset all filters
              </Button>
            ) : undefined
          }
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredLabs.map((lab, index) => {
            const labName = lab.lab_name || lab.name || 'BIS Testing Laboratory';
            const email = extractEmail(lab);
            const phone = extractPhone(lab);
            const website = extractWebsite(lab);
            const testedProducts = Array.isArray((lab as Record<string, unknown>).tested_products)
              ? ((lab as Record<string, unknown>).tested_products as string[])
              : [];

            return (
              <Card
                key={lab.id || index}
                className="p-4 md:p-5 flex flex-col justify-between space-y-4 hover:border-border-strong transition-colors"
              >
                <div className="space-y-3">
                  {/* Card Header: Name & Type Badge */}
                  <div className="flex items-start justify-between gap-3">
                    <div className="space-y-0.5">
                      <div className="flex items-center gap-1.5">
                        <Building2 className="w-3.5 h-3.5 text-brand-600 dark:text-brand-400 shrink-0" />
                        <span className="font-mono text-[11px] font-semibold uppercase tracking-wider text-text-tertiary">
                          {lab.id || `LAB-${index + 1}`}
                        </span>
                      </div>
                      <h3 className="text-base font-semibold leading-snug text-text-primary">
                        {labName}
                      </h3>
                    </div>

                    {lab.type && (
                      <Badge variant={getLabTypeVariant(lab.type)} className="text-[10px] shrink-0 max-w-[160px] truncate">
                        {lab.type}
                      </Badge>
                    )}
                  </div>

                  {/* Location & Address */}
                  {(lab.address || lab.city || lab.state) && (
                    <div className="flex items-start gap-2 text-xs text-text-secondary">
                      <MapPin className="w-3.5 h-3.5 mt-0.5 shrink-0 text-text-tertiary" />
                      <div className="space-y-0.5">
                        {lab.address && <p className="leading-relaxed">{lab.address}</p>}
                        <p className="font-medium text-text-primary">
                          {[lab.city, lab.state].filter(Boolean).join(', ')}
                        </p>
                      </div>
                    </div>
                  )}

                  {/* Accreditation */}
                  {lab.accreditation && (
                    <div className="p-2 rounded border border-border-subtle bg-bg-secondary text-xs flex items-center gap-2">
                      <ShieldCheck className="w-3.5 h-3.5 shrink-0 text-emerald-500" />
                      <span className="font-medium text-text-primary">
                        {lab.accreditation}
                      </span>
                    </div>
                  )}

                  {/* Disciplines Chips */}
                  {Array.isArray(lab.disciplines) && lab.disciplines.length > 0 && (
                    <div className="space-y-1">
                      <span className="text-[10px] font-semibold uppercase tracking-wider text-text-tertiary block">
                        Testing Disciplines
                      </span>
                      <div className="flex flex-wrap gap-1">
                        {lab.disciplines.map((d, i) => (
                          <span
                            key={i}
                            className="inline-flex items-center px-1.5 py-0.5 rounded text-[11px] font-medium border border-border-subtle bg-bg-secondary text-text-secondary"
                          >
                            {d}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Sample Tested Products (if available) */}
                  {testedProducts.length > 0 && (
                    <div className="space-y-1">
                      <span className="text-[10px] font-semibold uppercase tracking-wider text-text-tertiary block">
                        Key Tested Products
                      </span>
                      <p className="text-xs text-text-secondary leading-relaxed line-clamp-2">
                        {testedProducts.join(' • ')}
                      </p>
                    </div>
                  )}
                </div>

                {/* Card Footer: Action Links & Contact */}
                <div className="pt-3 border-t border-border-subtle flex flex-wrap items-center justify-between gap-3 text-xs">
                  <div className="flex flex-wrap items-center gap-3">
                    {email && (
                      <a
                        href={`mailto:${email}`}
                        className="inline-flex items-center gap-1 font-medium text-brand-600 dark:text-brand-400 hover:underline"
                        title={`Send email to ${email}`}
                      >
                        <Mail className="w-3 h-3" />
                        <span>{email}</span>
                      </a>
                    )}

                    {phone && (
                      <a
                        href={`tel:${phone}`}
                        className="inline-flex items-center gap-1 font-medium text-text-secondary hover:text-text-primary"
                        title={`Call ${phone}`}
                      >
                        <Phone className="w-3 h-3" />
                        <span>{phone}</span>
                      </a>
                    )}
                  </div>

                  {website && (
                    <a
                      href={website}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 font-medium text-brand-600 dark:text-brand-400 hover:underline"
                    >
                      <span>Lab Portal</span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  )}
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* ─── Bottom Information Note ─── */}
      <footer className="rounded-lg border border-border-subtle bg-bg-secondary p-4 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-text-secondary">
        <div className="flex items-center gap-2.5">
          <ShieldCheck className="w-4 h-4 shrink-0 text-emerald-500" />
          <span>
            Laboratories conform to <strong>ISO/IEC 17025</strong> general requirements for testing and
            calibration competencies, accredited by NABL.
          </span>
        </div>
        <a
          href="https://www.nabl-india.org"
          target="_blank"
          rel="noopener noreferrer"
          className="shrink-0 font-medium text-brand-600 dark:text-brand-400 hover:underline"
        >
          NABL Portal &rarr;
        </a>
      </footer>
    </div>
  );
}
