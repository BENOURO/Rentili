export default function Avatar({ user, size = '' }) {
  return (
    <span className={`avatar ${size}`}>
      {user?.avatar ? <img src={user.avatar} alt="" /> : user?.initials}
    </span>
  )
}
