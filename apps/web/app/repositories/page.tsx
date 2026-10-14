"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiClient, type Project, type Repository } from "@/lib/api-client";
import LoadingSpinner from "@/components/ui/LoadingSpinner";
import ErrorState from "@/components/ui/ErrorState";
import EmptyState from "@/components/ui/EmptyState";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";

import { useFeedback } from "@/components/ui/Feedback";
export default function RepositoriesPage() {
  const { toast, confirm } = useFeedback();
  const [projects, setProjects] = useState<Project[]>([]);
  const [reposByProject, setReposByProject] = useState<
    Record<string, Repository[]>
  >({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [addingTo, setAddingTo] = useState<string | null>(null);
  const [repoName, setRepoName] = useState("");
  const [repoUrl, setRepoUrl] = useState("");

  const fetchData = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const projRes = await apiClient.listProjects({ page_size: "100" });
      const projs = projRes.items || [];
      setProjects(projs);
      const repoMap: Record<string, Repository[]> = {};
      await Promise.all(
        projs.map(async (p: Project) => {
          try {
            const repos = await apiClient.listProjectRepos(p.id);
            if (repos && repos.length > 0) repoMap[p.id] = repos;
          } catch {
            /* ignore */
          }
        })
      );
      setReposByProject(repoMap);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleAddRepo = async (projectId: string) => {
    if (!repoName.trim() || !repoUrl.trim()) return;
    try {
      await apiClient.createRepo(projectId, {
        name: repoName.trim(),
        url: repoUrl.trim(),
        provider: "GITHUB",
        default_branch: "main",
      });
      setRepoName("");
      setRepoUrl("");
      setAddingTo(null);
      fetchData();
    } catch (err: unknown) {
      toast(err instanceof Error ? err.message : "Failed to add repo", "error");
    }
  };

  const handleDeleteRepo = async (repoId: string) => {
    if (!(await confirm({ title: "Remove this repository?" }))) return;
    try {
      await apiClient.deleteRepo(repoId);
      fetchData();
    } catch (err: unknown) {
      toast(
        err instanceof Error ? err.message : "Failed to remove repo",
        "error"
      );
    }
  };

  if (isLoading)
    return (
      <div className="flex justify-center py-12">
        <LoadingSpinner />
      </div>
    );
  if (error) return <ErrorState message={error} onRetry={fetchData} />;

  return (
    <div className="max-w-4xl mx-auto pb-12">
      <h1 className="text-2xl font-bold mb-6">Repositories</h1>

      {projects.length === 0 ? (
        <EmptyState
          title="No projects"
          description="Create a project first, then you can link repositories to it."
        />
      ) : (
        <div className="space-y-6">
          {projects.map((project) => (
            <div
              key={project.id}
              className="bg-[var(--sidebar-bg)] border border-[var(--sidebar-border)] rounded-xl p-5"
            >
              <div className="flex items-center justify-between mb-3">
                <Link
                  href={`/projects/${project.id}`}
                  className="font-semibold hover:text-[var(--primary)]"
                >
                  {project.name}
                </Link>
                <Button
                  variant="ghost"
                  onClick={() =>
                    setAddingTo(addingTo === project.id ? null : project.id)
                  }
                >
                  {addingTo === project.id ? "Cancel" : "+ Add Repo"}
                </Button>
              </div>

              {addingTo === project.id && (
                <div className="flex gap-3 mb-4">
                  <Input
                    placeholder="Repo name"
                    value={repoName}
                    onChange={(e) => setRepoName(e.target.value)}
                  />
                  <Input
                    placeholder="https://github.com/..."
                    value={repoUrl}
                    onChange={(e) => setRepoUrl(e.target.value)}
                  />
                  <Button onClick={() => handleAddRepo(project.id)}>Add</Button>
                </div>
              )}

              {(reposByProject[project.id] || []).length > 0 ? (
                <div className="space-y-2">
                  {reposByProject[project.id].map((repo: Repository) => (
                    <div
                      key={repo.id}
                      className="flex items-center justify-between p-3 border border-[var(--sidebar-border)] rounded-lg"
                    >
                      <div>
                        <span className="font-medium text-sm">{repo.name}</span>
                        <a
                          href={repo.url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-xs text-[var(--primary)] hover:underline ml-3"
                        >
                          {repo.url}
                        </a>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="text-xs text-[var(--text-muted)]">
                          {repo.provider} · {repo.default_branch}
                        </span>
                        <button
                          onClick={() => handleDeleteRepo(repo.id)}
                          className="text-xs text-red-400 hover:text-red-300"
                        >
                          Remove
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-[var(--text-muted)]">
                  No repositories linked.
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
