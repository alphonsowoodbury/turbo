import { FileQuestion } from "lucide-react";
import Link from "next/link";

export default function NotFound() {
  return (
    <div className="flex h-full items-center justify-center p-6">
      <div className="text-center max-w-md space-y-4">
        <FileQuestion className="h-12 w-12 mx-auto text-muted-foreground" />
        <h2 className="text-lg font-semibold">Page not found</h2>
        <p className="text-sm text-muted-foreground">
          The page you&apos;re looking for doesn&apos;t exist or has been moved.
        </p>
        <Link
          href="/"
          className="inline-flex items-center text-sm text-primary hover:underline"
        >
          Back to dashboard
        </Link>
      </div>
    </div>
  );
}
