import { Link } from 'react-router-dom'
import Avatar from '../../components/Avatar'
import { monthYear } from './format'

export default function MemberCard({ member }) {
  return (
    <Link className="member-card" to={`/membres/${member.id}`}>
      <Avatar user={member} size="md" />
      <div>
        <b>{member.display_name}</b>
        <div className="muted small">{member.city || 'Ville non renseignée'}</div>
        <div className="muted small">Membre depuis {monthYear(member.date_joined)}</div>
      </div>
    </Link>
  )
}
