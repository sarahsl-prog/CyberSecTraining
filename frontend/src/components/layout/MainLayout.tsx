import React from 'react';
import { Outlet } from 'react-router-dom';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { SkipLink } from '@/components/common/SkipLink';
import styles from './MainLayout.module.css';

export function MainLayout() {
  return (
    <div className={styles.layout}>
      {/* Skip link for keyboard navigation - first focusable element */}
      <SkipLink href="#main-content">Skip to main content</SkipLink>

      <Header />

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
