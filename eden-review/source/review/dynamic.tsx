import { lazy, Suspense, type ComponentType } from "react";

// Equivalent client-side lazy loading for the standalone HTML review build.
// The production Next/Vinext entry point keeps its own next/dynamic import.
export default function dynamic<P extends object>(
  load: () => Promise<ComponentType<P>>,
  options: { loading?: ComponentType; ssr?: boolean } = {},
) {
  const Component = lazy(async () => ({ default: await load() }));
  const Loading = options.loading;
  return function DynamicComponent(props: P) {
    return <Suspense fallback={Loading ? <Loading /> : null}><Component {...props} /></Suspense>;
  };
}
