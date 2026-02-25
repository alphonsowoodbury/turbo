// Generate stub API files
const fs = require('fs');
const path = require('path');

const apiModules = [
  'issues', 'mentors', 'action-approvals', 'agents', 'blueprints',
  'comments', 'terminal', 'favorites', 'initiatives', 'literature',
  'milestones', 'notes', 'podcasts', 'saved-filters', 'scripts',
  'skills', 'my-queue', 'staff', 'tags', 'documents', 'work-queue',
  'discoveries', 'calendar', 'worktrees', 'forms', 'approvals',
  'job-search', 'job-applications', 'resumes', 'network-contacts',
  'companies'
];

const template = (moduleName) => `import { apiClient } from "./client";

export const ${moduleName}Api = {
  async list(params?: any): Promise<any[]> {
    const { data } = await apiClient.get("/${moduleName.replace('Api', '')}/", { params });
    return data;
  },

  async get(id: string): Promise<any> {
    const { data } = await apiClient.get(\`/${moduleName.replace('Api', '')}/\${id}\`);
    return data;
  },

  async create(item: any): Promise<any> {
    const { data } = await apiClient.post("/${moduleName.replace('Api', '')}/", item);
    return data;
  },

  async update(id: string, updates: any): Promise<any> {
    const { data } = await apiClient.put(\`/${moduleName.replace('Api', '')}/\${id}\`, updates);
    return data;
  },

  async delete(id: string): Promise<void> {
    await apiClient.delete(\`/${moduleName.replace('Api', '')}/\${id}\`);
  },
};

export default ${moduleName}Api;
`;

const apiDir = path.join(__dirname, 'api');

apiModules.forEach(module => {
  const fileName = `${module}.ts`;
  const filePath = path.join(apiDir, fileName);

  if (!fs.existsSync(filePath)) {
    const camelCase = module.replace(/-([a-z])/g, (g) => g[1].toUpperCase());
    fs.writeFileSync(filePath, template(camelCase));
    console.log(`Created ${fileName}`);
  }
});

console.log('API files generated successfully!');
