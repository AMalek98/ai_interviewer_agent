/**
 * Language Mapper Utility
 * Maps backend technology names to Monaco Editor language identifiers
 */

export const getMonacoLanguage = (technology) => {
  if (!technology) return 'python'; // Default fallback

  const langMap = {
    'python': 'python',
    'javascript': 'javascript',
    'typescript': 'typescript',
    'java': 'java',
    'c#': 'csharp',
    'csharp': 'csharp',
    'go': 'go',
    'rust': 'rust',
    'php': 'php',
    'ruby': 'ruby',
    'sql': 'sql',
    'postgresql': 'sql',
    'mysql': 'sql',
    'mongodb': 'javascript', // MongoDB queries use JS syntax
    'nosql': 'javascript',
    'redis': 'redis',
    'html': 'html',
    'css': 'css',
    'json': 'json',
    'xml': 'xml',
    'yaml': 'yaml',
    'markdown': 'markdown'
  };

  return langMap[technology.toLowerCase()] || 'python'; // Default fallback
};
