import fs from 'fs';
import path from 'path';
import yaml from 'js-yaml';

export interface PageDef {
  id: number;
  slug: string;
  title: string;
}

export interface SubToolDef {
  name: string;
  source: string;
  category: string;
}

interface SlidesData {
  pages: PageDef[];
  sub_tools: SubToolDef[];
}

function loadData(): SlidesData {
  const dataPath = path.resolve(process.cwd(), 'src/data/slides-data.yaml');
  const raw = fs.readFileSync(dataPath, 'utf-8');
  return yaml.load(raw) as SlidesData;
}

export function getPages(): PageDef[] {
  return loadData().pages;
}

export function getSubTools(): SubToolDef[] {
  return loadData().sub_tools;
}

export function getPageById(id: number): PageDef | undefined {
  return getPages().find(p => p.id === id);
}

export function getAdjacentPages(currentId: number): { prev: PageDef | null; next: PageDef | null } {
  const pages = getPages();
  const index = pages.findIndex(p => p.id === currentId);
  return {
    prev: index > 0 ? pages[index - 1] : null,
    next: index < pages.length - 1 ? pages[index + 1] : null,
  };
}
