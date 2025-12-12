import React from 'react';
import { Outlet } from 'react-router-dom';
import { Header } from './Header';
import { ModeBanner } from './ModeBanner';
import { Sidebar } from './Sidebar';
import { SkipLink } from '@/components/common/SkipLink';
import styles from './MainLayout.module.css';

export function MainLayout() {
  return (
    <div className={styles.layout}>
      {/* Skip link for keyboard navigation - first focusable element */}
      <SkipLink href="#main-content">Skip to main content</SkipLink>

      <Header />

      {/* Mode banner - shows training vs live mode */}
      <ModeBanner />

      <div className={styles.body}>
        <Sidebar />

        <main id="main-content" className={styles.main} tabIndex={-1}>
          <Outlet />
        </main>
      </div>
    </div>
  );
}

export default MainLayout;
