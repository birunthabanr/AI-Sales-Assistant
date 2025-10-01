import React from 'react'
import DashboardPage from '../../src/pages/Dashboard'
import { mount } from 'cypress/react'
import { MemoryRouter } from 'react-router-dom'

describe('<DashboardPage />', () => {
  it('renders', () => {
    mount(
    <MemoryRouter>
      <DashboardPage />
    </MemoryRouter>
    )
  })
})