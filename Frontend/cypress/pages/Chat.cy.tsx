import React from 'react'
import { MemoryRouter } from 'react-router-dom'
import Chat from '../../src/pages/Chat'
import { mount } from 'cypress/react'

describe('<Chat />', () => {
  it('renders', () => {
    mount(
      <MemoryRouter>
        <Chat />
      </MemoryRouter>
    )
  })
})



